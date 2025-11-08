"""
OAuth2 Configuration cho Google, Twitter, GitHub
"""
import os
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

oauth = OAuth()

# Google OAuth
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET', ''),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# GitHub OAuth
oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID', ''),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET', ''),
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri='http://127.0.0.1:8000/auth/github/callback',
    client_kwargs={'scope': 'user:email'},
)

# Twitter OAuth (OAuth 2.0)
oauth.register(
    name='twitter',
    client_id=os.getenv('TWITTER_CLIENT_ID', ''),
    client_secret=os.getenv('TWITTER_CLIENT_SECRET', ''),
    authorize_url='https://twitter.com/i/oauth2/authorize',
    authorize_params={'code_challenge_method': 'S256'},
    access_token_url='https://api.twitter.com/2/oauth2/token',
    redirect_uri='http://127.0.0.1:8000/auth/twitter/callback',
    client_kwargs={'scope': 'tweet.read users.read'},
)
