import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
	long_description = fh.read()

setuptools.setup(
	name='coderone-challenge-dungeon',
	version='0.1.5',
	description='Dungeons and data structures: Coder one AI Game Tournament',
	url='https://github.com/gocoderone/dungeons-and-data-structures',
	author='Ivan Ryabov',
	author_email='HUMANS@gocoder.one',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
	install_requires=[
		'pymunk==5.7.0',
		'appdirs==1.4.4',
		'arcade==2.4.3',
		'watchdog==0.10.4',
		'jsonplus==0.8.0',

		'requests==2.25.0'
	],
    python_requires='>=3.6',
	entry_points = {
        'console_scripts': [
			'coderone=coderone.cli:main',
			'coderone-dungeon=coderone.dungeon.main:main'
		],
    },
	
	zip_safe=False,
	package_data = {
		'coderone.dungeon': [
			'assets/sounds/explosion.mp3',

			'assets/images/bomb_64px.png',
			'assets/images/ammo.png',
			'assets/images/chest.png',
			'assets/images/crate.png',
			'assets/images/ore_block.png',
			'assets/images/metal_block.png',
			'assets/images/skelet_run_anim_f1.png',
			'assets/images/coin_anim_f0.png',
			'assets/images/explosion.png',

			'assets/images/floor_1.png',
			'assets/images/floor_2.png',
			'assets/images/floor_3.png',
			'assets/images/floor_4.png',
			'assets/images/floor_5.png',
			'assets/images/floor_6.png',
			'assets/images/floor_7.png',
			'assets/images/floor_8.png',

			'assets/images/p1_knight_64px.png',
			'assets/images/p2_knight_64px.png',
			'assets/images/p2_knight_64px_flipped.png',
			'assets/images/p2_knight_orange_64px_flipped.png',
			'assets/images/wizard_m_64px.png',
			'assets/images/wizard_f_64px.png',

			"assets/images/chrome/wall_side_top_left.png",
			"assets/images/chrome/wall_side_top_right.png",
			"assets/images/chrome/wall_side_front_left.png",
			"assets/images/chrome/wall_side_front_right.png",

			"assets/images/chrome/wall_corner_top_left.png",
			"assets/images/chrome/wall_corner_top_right.png",

			"assets/images/chrome/wall_corner_front_left.png",
			"assets/images/chrome/wall_corner_front_right.png",

			"assets/images/chrome/wall_top_left.png",
			"assets/images/chrome/wall_top_mid.png",
			"assets/images/chrome/wall_top_right.png",
			"assets/images/chrome/wall_side_mid_left.png",
			"assets/images/chrome/wall_mid.png",
			"assets/images/chrome/wall_side_mid_right.png",

		]
	},
)