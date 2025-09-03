#!/usr/bin/env python3
"""
Fine-tuning script for tractionbuild summarization model.
Uses Unsloth for efficient fine-tuning of Llama 3.1 8B.
"""

import os
import sys
import json
from pathlib import Path
from datasets import Dataset
from unsloth import FastLanguageModel
import torch
from transformers import TrainingArguments
from trl import SFTTrainer
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_summarization_dataset(data_path: str = "data/summarization_dataset.json") -> Dataset:
    """
    Load and prepare the summarization dataset.
    
    Args:
        data_path: Path to the JSON dataset file
        
    Returns:
        HuggingFace Dataset object
    """
    try:
        # Load the JSON dataset
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to the format expected by the model
        formatted_data = []
        for item in data:
            formatted_data.append({
                "text": f"Summarize the following text:\n\n{item['input']}\n\nSummary:",
                "target": item['output']
            })
        
        # Create HuggingFace dataset
        dataset = Dataset.from_list(formatted_data)
        logger.info(f"Loaded dataset with {len(dataset)} examples")
        
        return dataset
        
    except FileNotFoundError:
        logger.error(f"Dataset file not found: {data_path}")
        # Create a small sample dataset for testing
        sample_data = [
            {
                "text": "Summarize the following text:\n\nAI is transforming the way we work and live. From virtual assistants to autonomous vehicles, artificial intelligence is becoming increasingly integrated into our daily lives.\n\nSummary:",
                "target": "AI is revolutionizing work and daily life through various applications like virtual assistants and autonomous vehicles."
            },
            {
                "text": "Summarize the following text:\n\nStartup companies are driving innovation across industries. These young companies often bring fresh perspectives and disruptive technologies that challenge established business models.\n\nSummary:",
                "target": "Startups drive innovation by bringing fresh perspectives and disruptive technologies to challenge established businesses."
            }
        ]
        
        dataset = Dataset.from_list(sample_data)
        logger.info(f"Created sample dataset with {len(dataset)} examples")
        return dataset

def fine_tune_model(
    dataset: Dataset,
    model_name: str = "unsloth/llama-3.1-8b-bnb-4bit",
    output_dir: str = "models/fine_tuned_summarizer",
    num_epochs: int = 3,
    batch_size: int = 2,
    learning_rate: float = 2e-4
) -> None:
    """
    Fine-tune the summarization model.
    
    Args:
        dataset: Training dataset
        model_name: Base model to fine-tune
        output_dir: Directory to save the fine-tuned model
        num_epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate for training
    """
    try:
        logger.info(f"Loading base model: {model_name}")
        
        # Load the base model with 4-bit quantization
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_name,
            max_seq_length=2048,
            dtype=None,  # Auto-detect
            load_in_4bit=True,
        )
        
        # Prepare the model for training
        model = FastLanguageModel.get_peft_model(
            model,
            r=16,  # Rank
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj"],
            lora_alpha=16,
            lora_dropout=0,
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=3407,
            use_rslora=False,
            loftq_config=None,
        )
        
        # Tokenize the dataset
        def tokenize_function(examples):
            # Combine text and target
            combined_texts = [f"{text}\n\nSummary: {target}" for text, target in zip(examples["text"], examples["target"])]
            
            # Tokenize
            tokenized = tokenizer(
                combined_texts,
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors="pt"
            )
            
            # Create labels (same as input_ids for causal language modeling)
            tokenized["labels"] = tokenized["input_ids"].clone()
            
            return tokenized
        
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            learning_rate=learning_rate,
            fp16=True,
            logging_steps=10,
            save_steps=100,
            save_total_limit=2,
            remove_unused_columns=False,
            push_to_hub=False,
            report_to=None,  # Disable wandb/tensorboard
        )
        
        # Initialize trainer
        trainer = SFTTrainer(
            model=model,
            train_dataset=tokenized_dataset,
            tokenizer=tokenizer,
            args=training_args,
            max_seq_length=512,
            dataset_text_field="text",
        )
        
        logger.info("Starting fine-tuning...")
        trainer.train()
        
        # Save the fine-tuned model
        logger.info(f"Saving fine-tuned model to {output_dir}")
        trainer.save_model(output_dir)
        tokenizer.save_pretrained(output_dir)
        
        # Save training config
        config = {
            "base_model": model_name,
            "num_epochs": num_epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "dataset_size": len(dataset),
            "max_seq_length": 512,
            "training_args": training_args.to_dict()
        }
        
        with open(os.path.join(output_dir, "training_config.json"), 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info("Fine-tuning completed successfully!")
        
    except Exception as e:
        logger.error(f"Fine-tuning failed: {e}")
        raise

def create_ollama_model(model_path: str, model_name: str = "tractionbuild-summarizer") -> None:
    """
    Create an Ollama model from the fine-tuned model.
    
    Args:
        model_path: Path to the fine-tuned model
        model_name: Name for the Ollama model
    """
    try:
        # Create Modelfile for Ollama
        modelfile_content = f"""FROM {model_path}
TEMPLATE """{{"Summarize the following text:\n\n{{.Input}}\n\nSummary:"}}"""
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER max_tokens 150
SYSTEM You are a helpful assistant that creates concise summaries of text. Always provide clear, accurate summaries in 150 words or less.
"""
        
        modelfile_path = os.path.join(model_path, "Modelfile")
        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)
        
        logger.info(f"Created Modelfile at {modelfile_path}")
        logger.info(f"To create Ollama model, run: ollama create {model_name} {modelfile_path}")
        
    except Exception as e:
        logger.error(f"Failed to create Ollama model: {e}")

def main():
    """Main function to run the fine-tuning process."""
    logger.info("Starting tractionbuild summarization model fine-tuning")
    
    # Create output directory
    output_dir = "models/fine_tuned_summarizer"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load dataset
    dataset = load_summarization_dataset()
    
    # Fine-tune the model
    fine_tune_model(
        dataset=dataset,
        output_dir=output_dir,
        num_epochs=3,
        batch_size=2,
        learning_rate=2e-4
    )
    
    # Create Ollama model
    create_ollama_model(output_dir)
    
    logger.info("Fine-tuning process completed!")

if __name__ == "__main__":
    main()
