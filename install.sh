sudo apt update && apt upgrade -y
sudo apt install -y python3 python3-pip
pip3 install -r requirements.txt
echo 'export PATH="/home/$USER/.local/bin:$PATH"' >> ../.bashrc
source .bashrc
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list
sudo apt update
sudo apt install -y elasticsearch
#pip install elasticsearch
#pip install beebotte