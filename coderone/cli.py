##!/usr/bin/env python
"""
 Coder One CLI
"""
import fire


class CoderOneCli(object):

	def submit(self, team: str, package: str):
		"""Submit the Agent code/package for the team entry in the
		trournament"""
		print(f"Team: '{team}'")
		print(f"Agent-module: '{package}'")

		print("!Not implemented yet")
		return

	def status(self, team: str, package: str):
		"""Check the status of your code submission
		"""
		return


def main():
	fire.Fire(CoderOneCli())

if __name__ == '__main__':
	main()