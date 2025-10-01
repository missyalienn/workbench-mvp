#!/usr/bin/env python3
"""Simple Reddit API authentication test"""

import os
import praw
import keyring

#OLD: Get credentials from environment
#client_id = os.getenv('REDDIT_CLIENT_ID')
#client_secret = os.getenv('REDDIT_CLIENT_SECRET')
#user_agent = 'TestScript/1.0 by /u/chippetto90'

#NEW: Get credentials from Keychain 
client_id = keyring.get_password("reddit-client-id", "reddit-api")
client_secret = keyring.get_password("reddit-client-secret", "reddit-api")
user_agent = "TestScript/1.0 by /u/chippetto90"

print("Testing Reddit API authentication...")
print(f"Client ID: {client_id[:10]}..." if client_id else "Client ID: NOT FOUND")
print(f"Client Secret: {'SET' if client_secret else 'NOT FOUND'}")

if not client_id or not client_secret:
    print("❌ Missing credentials - export them first")
    if __name__ == "__main__":
        exit(1)
    else:
        # Skip test if credentials not available
        import unittest
        class TestAuth(unittest.TestCase):
            def test_auth_skipped(self):
                self.skipTest("Reddit credentials not available")
        unittest.main(exit=False)
        #return

try:
    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent, read_only=True)
    subreddit = reddit.subreddit('diy')
    test_posts = list(subreddit.hot(limit=1))
    
    if test_posts:
        print("✅ Authentication successful!")
        print(f"Test post: {test_posts[0].title[:50]}...")
    else:
        print("❌ No posts returned")
        
except Exception as e:
    print(f"❌ Authentication failed: {e}")
