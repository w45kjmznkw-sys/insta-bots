import os
import time
from instagrapi import Client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InstagramFollowBot:
    def __init__(self):
        self.cli = Client()
        self.session_file = "session.json"
        
        # Try to load session to avoid re-login
        try:
            self.cli.load_settings(self.session_file)
            self.cli.login(os.getenv("INSTAGRAM_USERNAME"), os.getenv("INSTAGRAM_PASSWORD"))
            logger.info("Logged in successfully using saved session.")
        except Exception as e:
            logger.warning(f"Session failed. Logging in fresh... Error: {e}")
            self.cli.login(os.getenv("INSTAGRAM_USERNAME"), os.getenv("INSTAGRAM_PASSWORD"))
            self.cli.dump_settings(self.session_file)

    def follow_user(self, username):
        """Follows a specific user."""
        try:
            user_id = self.cli.user_id_from_username(username)
            self.cli.follow(user_id)
            logger.info(f"✅ Successfully followed @{username}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to follow @{username}: {e}")
            return False

    def get_followers(self, username):
        """Gets a list of users who follow a target account."""
        try:
            user_id = self.cli.user_id_from_username(username)
            followers = self.cli.user_followers(user_id)
            return followers
        except Exception as e:
            logger.error(f"❌ Failed to get followers for @{username}: {e}")
            return []

    def unfollow_non_followers(self, max_unfollow=50):
        """Unfollows people who don't follow you back."""
        try:
            my_followers = set(self.get_followers(self.cli.username))
            my_following = self.cli.user_following(self.cli.username)
            
            unfollowed_count = 0
            for user in my_following:
                if user.pk not in my_followers:
                    try:
                        self.cli.unfollow(user.pk)
                        logger.info(f"🔻 Unfollowed @{user.username} (didn't follow back)")
                        unfollowed_count += 1
                        time.sleep(2) 
                        if unfollowed_count >= max_unfollow:
                            break
                    except Exception as e:
                        logger.error(f"Error unfollowing {user.username}: {e}")
                        continue
            logger.info(f"Finished unfollowing. Total: {unfollowed_count}")
        except Exception as e:
            logger.error(f"Error in unfollow loop: {e}")

    def follow_target_followers(self, target_username, count=10):
        """Follows people who follow a specific target account."""
        followers = self.get_followers(target_username)
        followed_count = 0
        
        for follower in followers[:count]:
            if self.cli.username != follower.username:
                if self.follow_user(follower.username):
                    followed_count += 1
                    delay = 5 + (hash(str(time.time())) % 6)
                    time.sleep(delay)
                    
        logger.info(f"Completed following {followed_count} users from @{target_username}")

    def run_daily_cycle(self, targets=None, max_unfollow=50):
        """Main cycle: Unfollow non-followers, then follow target audiences."""
        logger.info("Starting daily cycle...")
        
        # 1. Clean up your own following list
        self.unfollow_non_followers(max_unfollow)
        
        # 2. Follow competitors/targets
        if targets:
            for target in targets:
                logger.info(f"Analyzing competitor: @{target}")
                self.follow_target_followers(target, count=10)
                time.sleep(30)
                
        logger.info("Daily cycle complete.")

if __name__ == "__main__":
    # --- CONFIGURATION ---
    INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
    INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
    
    # List of accounts whose followers you want to steal/follow
    TARGET_ACCOUNTS = ["competitor1", "competitor2", "niche_account"]
    
    # How many people to unfollow who don't follow back
    MAX_UNFOLLOW = 50
    
    bot = InstagramFollowBot()
    bot.run_daily_cycle(targets=TARGET_ACCOUNTS, max_unfollow=MAX_UNFOLLOW)
