#!/usr/bin/env bash
SCRIPTS="/home/$USER/.scripts"

if [ ! -e /home/$USER/odoo-tools ]; then
	echo "Cloning repo jklgrasso/odoo-tools"
	git clone https://github.com/jklgrasso/odoo-tools /home/$USER/odoo-tools
else
	 echo "Repo already downloaded"
fi

echo "Moving..."
mkdir -p $SCRIPTS
cp -r /home/$USER/odoo-tools/chk-odoo-dups.py ~/.scripts
sudo cp -r /home/$USER/odoo-tools/chk-odoo-dups /usr/bin/
cp -r /home/$USER/odoo-tools/chk-odoo-dups.desktop /home/$USER/.local/share/applications/

if [ -e $SCRIPTS ]; then
	if [ -e /home/$USER/.local/share/applications/chk-odoo-dups.desktop ]; then
		if [ -e $SCRIPTS/chk-odoo-dups.py ]; then
			if [ -e /usr/bin/chk-odoo-dups ]; then
				echo "Removing repo"
				mv /home/$USER/odoo-tools /home/$USER/.scripts/

				echo "Installing dependencies"
				sleep 2

				sudo apt update
				sudo apt install gpg -y
				sudo apt install python3-pip -y
				pip install python-gnupg
				clear
				echo "Done installing"
				echo "Close this terminal and search for Check Odoo SN Duplicates in the launcher."
			else
				echo "Failed at chk-odoo-serials"
				exit
			fi
		else
			 echo "Failed at odoo-dups"
			exit
		fi
	else
		 echo "Failed at chk-odoo-dups.desktop"
		exit
	fi
else
	 echo "Failed at .scripts"
	exit
fi
