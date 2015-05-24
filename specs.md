Notice
======
The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

This file is released under same licence as the engine. For the licence, look at `licence.txt`.

Game Engine
===========
VERSION 0.2.2



Game Package Specification
==========================

Game package is single folder that contains all game files.

All xml files MUST be valid xml, with following exceptions.
* HTML-style comments are allowed.
* You MAY use printable UTF-8 characters in addition to ASCII characters.


`main.xml`
----------
`main.xml` contains game settings and metadata.

File MUST contain following tags:
* `main`
* `settings`
* `startroom` (in `settings`)

Example file:

	<main>
		<meta author="John Smith"/>
		<meta created="2015-04-28"/>
		<description>
			Description of game.
		</description>
		<settings>
			<startroom file="first_room.xml"/>
		</settings>
		<intro>
			Welcome to example game.
		</intro>
	</main>

Room file
---------
Room file contains data for single room.

File MUST contain following tags:
* `description`
* `items`
* `doors`

Example file:

	<room name="FirstRoom">
		<description>
			Example room description.
		</description>
		<items>
			<item name="solapullo"/>
		</items>
		<doors>
			<door file="second_room.xml" direction="north" locked="0"/>
			<door file="third_room.xml" direction="west" locked="1"/>
		</doors>
		<script file="first_room.py"/>
	</room>

Script file
-----------
Script file contains python script that can be used to create additional functionality. Script files MUST have file name extension `py` and they MUST be valid Python files. The version of python is same as the version that is installed on the system.

Script file must have following functions:
* `onenter(dict variables, list inventory, list items)` &#8594; `dict variables, list inventory, list items`
* `oncommand(str command, dict variables, list inventory, list items)` &#8594; `bool result, dict variables, list inventory, list items`

The `bool result` of oncommand describes wheter command succeeded or not. It MUST be `True` on success and `False` otherwise.
