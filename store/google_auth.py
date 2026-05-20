"""
Google OAuth 2.0 Authentication Views
"""
import urllib.parse
import urllib.request
import json
from django.shortcuts import redirect
from django.conf import settings
from django.http import HttpResponse


def google_login_redirect(request):
    """
    Google OAuth page pe redirect karo
    """
    client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'online',
        'prompt': 'select_account',  # Har baar account select karne ka option
    }

    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
    return redirect(auth_url)


def google_callback(request):
    """
    Google se wapas aane ke baad user info fetch karo aur session mein save karo
    """
    code = request.GET.get('code')
    error = request.GET.get('error')

    if error or not code:
        return redirect('/auth/?google_error=1')
    client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    client_secret = settings.GOOGLE_OAUTH_CLIENT_SECRET
    redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI

    # Step 1: Code ko access token se exchange karo
    token_data = urllib.parse.urlencode({
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }).encode('utf-8')

    try:
        token_req = urllib.request.Request(
            'https://oauth2.googleapis.com/token',
            data=token_data,
            method='POST'
        )
        token_req.add_header('Content-Type', 'application/x-www-form-urlencoded')

        with urllib.request.urlopen(token_req) as resp:
            token_response = json.loads(resp.read().decode('utf-8'))

        access_token = token_response.get('access_token')
        if not access_token:
            return redirect('/auth/?google_error=1')

        # Step 2: Access token se user info fetch karo
        userinfo_req = urllib.request.Request(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        with urllib.request.urlopen(userinfo_req) as resp:
            user_info = json.loads(resp.read().decode('utf-8'))

        # Step 3: User data session mein save karo
        request.session['google_user'] = {
            'id': user_info.get('id'),
            'name': user_info.get('name', ''),
            'email': user_info.get('email', ''),
            'picture': user_info.get('picture', ''),
            'given_name': user_info.get('given_name', ''),
            'family_name': user_info.get('family_name', ''),
            'loggedIn': True,
            'provider': 'google',
        }

        # Auth page pe redirect karo with success flag
        return redirect('/auth/?google_success=1')

    except Exception as e:
        print(f"Google OAuth Error: {e}")
        return redirect('/auth/?google_error=1')


def google_clear_session(request):
    """
    Google user session clear karo after sessionStorage mein save ho jaye
    """
    if request.method == 'POST':
        if 'google_user' in request.session:
            del request.session['google_user']
    from django.http import JsonResponse
    return JsonResponse({'ok': True})
