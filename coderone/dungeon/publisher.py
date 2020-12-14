from typing import Dict, List, Tuple, Union, NamedTuple, Any, Optional
import getpass
import tarfile
import tempfile
import os
import sys

import jsonplus
import requests


BASE_URL = 'https://us-central1-psyched-equator-297906.cloudfunctions.net'
# BASE_URL = 'http://localhost:5001/psyched-equator-297906/us-central1'


class AuthInfo(NamedTuple):
	user_email:str
	token:str
	team_id:str
	team_name:str

def _yes_or_no(question):
	while "the answer is invalid":
		reply = str(input(question + ' (Y/n): ')).lower().strip()
		if not reply or reply[0] == 'y':
			return True
		if reply[0] == 'n':
			return False


class AuthError(Exception):
	pass


def _auth_team(user_email, passw) -> AuthInfo:
	print(f"Logging as '{user_email}'")

	user_r = requests.post(f'{BASE_URL}/auth', 
		data = {"email":user_email,"password":passw,"returnSecureToken": True}
	)

	response_json = user_r.json()
	if 'idToken' not in response_json:
		raise AuthError('Unauthorised' if 'error' not in response_json else response_json['error']['message'])
	
	user_token = response_json['idToken']
	r = requests.get(f'{BASE_URL}/api/my-team', headers = {"authorization": f"Bearer {user_token}"})
	if r.status_code != 200:	
		try:
			r.raise_for_status()
		except requests.exceptions.HTTPError:
			raise AuthError("Could not find participants team")

	team_info = r.json()
	print(team_info)

	team_id = team_info['teamId']
	if not team_id:
		raise AuthError("Could not find participants team")

	return AuthInfo(
			user_email = response_json['email'],
			token = user_token,
			team_id = team_id,
			team_name = team_info['teamName']
		)


def _submit_agent_code(module_archive, agent_name, single, auth:AuthInfo):
	print(f"Uploading agent archive '{agent_name}'")

	r = requests.put(f'{BASE_URL}/api/upload_url/{auth.team_id}/{agent_name}', params={'filename': f'{agent_name}.tar.gz', 'single': single}, headers = {"authorization": f"Bearer {auth.token}"})
	if r.status_code == 200:
		pass
	elif r.status_code == 401:
		response_json = r.json()
		print(f"❌ {response_json['message']}. Please check team Id and that you are a member of that team", file=sys.stderr)
		return
	else:
		try:
			r.raise_for_status()
		except requests.exceptions.HTTPError as ex:
			print(f"❌ Error uploading submission file: {ex}", file=sys.stderr)
			return

	response_json = r.json()
	upload_url = response_json['upload_url']

	r = requests.put(upload_url, module_archive, headers = {'Content-Type': 'application/octet-stream'})
	if r.status_code == 200:
		print('✓ Done.')
	else: 
		try:
			r.raise_for_status()
		except requests.exceptions.HTTPError as ex:
			print(f"❌ Error uploading submission file: {ex}", file=sys.stderr)
			return


def submit(agent_module:str, single:bool, source_file:str):
	""" Submit agent module for the team entry into the tournament.
	"""
	print(f"Submitting your agent '{agent_module}' for the tournament entry.")
	user_id = input("User email: ")
	passw = input("Submission token: ") # getpass.getpass(prompt='submission token: ')

	try:
		auth_info = _auth_team(user_id, passw)
	except AuthError as ex:
		print(f"❌ Failed: {ex}")
		return
	
	print(f"Submitting {'single-file' if single else 'module'} agent: '{agent_module}' for team '{auth_info.team_name}' by user '{auth_info.user_email}'")
	
	confirmed = _yes_or_no('Are this details correct?')
	if not confirmed:
		print("Canceled. No files submitted")
		return

	with tempfile.NamedTemporaryFile(suffix='.tar.gz') as f:
		with tarfile.open(fileobj=f, mode='w:gz') as tar:
			tar.add(source_file, arcname=os.path.basename(source_file))

		f.flush()
		f.seek(0)

		_submit_agent_code(f, agent_name=agent_module, single=single, auth=auth_info)
