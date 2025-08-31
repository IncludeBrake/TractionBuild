from typing import Dict, Any, List
from pydantic import BaseModel, Field
from ..vendors.salem import Salem

class MarketingPack(BaseModel):
    positioning: str
    landing_copy: str
    twitter: List[str] = Field(default_factory=list)
    linkedin: List[str] = Field(default_factory=list)
    email_seed: str
    youtube_script: str

class SalemMarketingTool:
    name = "Salem Marketing Asset Generator"
    description = "Generates high-quality marketing assets using Salem"

    async def _run(self, product_description: str, avatar: str, hooks: int = 3) -> Dict[str, Any]:
        # Salem is synchronous; call within async wrapper
        s = Salem()
        # Your Salem has many methods; keep it lean and deterministic
        hooks_list = s.translate_features_to_hooks(product_description, target_avatar=avatar, n=hooks)

        landing = s.generate_landing_page_copy(product_description, avatar)
        tweets = s.generate_x_tweets_for_avatar(avatar, hooks_list)
        linkedin = s.generate_linkedin_post_sequence(avatar, hooks_list)
        email = s.email_sequence_top_funnel(avatar, hooks_list)  # take first/mail-1
        yt = s.create_youtube_script_intro(hooks_list)

        pack = MarketingPack(
            positioning=f"AI product team for {avatar}",
            landing_copy=landing["hero_copy"] if isinstance(landing, dict) and "hero_copy" in landing else str(landing),
            twitter=(tweets.get("tweets") if isinstance(tweets, dict) else tweets) or [],
            linkedin=(linkedin.get("posts") if isinstance(linkedin, dict) else linkedin) or [],
            email_seed=(email.get("sequence")[0] if isinstance(email, dict) and email.get("sequence") else str(email)),
            youtube_script=(yt.get("youtube_script") if isinstance(yt, dict) else str(yt)),
        ).model_dump()

        return {"kind": "marketing_pack", "artifact": pack}
