import shutil
from os import system
print('Creating admin user...')
admin=input('Admin username: ')
admin_pass=input('Admin password: ')

print('Creating network share user:')
share_user=input('Network share user: ')
share_password=input('Network share password: ')

def gensshkey():
    print('Generating RSA key log SSH admin')
    system('ssh-keygen -t rsa -b 4096 -f ./KEY')
    

gensshkey()
def openssl():
    print('Creating RSA key for SSH...')
    system('openssl req -x509 -nodes -days 365 -newkey rsa:4096 -keyout ./key -out ./key')
openssl()    

def vsftpdconf():
    string = """
listen=YES
listen_ipv6=NO
connect_from_port_20=YES
anonymous_enable=NO
local_enable=YES
write_enable=YES
chroot_local_user=YES
allow_writeable_chroot=YES
secure_chroot_dir=/var/run/vsftpd/empty
pam_service_name=vsftpd
pasv_enable=YES
pasv_min_port=40000
pasv_max_port=45000
userlist_enable=YES
userlist_file=/etc/vsftpd.userlist
userlist_deny=NO
rsa_cert_file=/etc/key
rsa_private_key_file=/etc/key
ssl_enable=YES
force_local_data_ssl=YES
force_local_logins_ssl=YES
    """
    file = open('vsftpd.conf', 'w')
    file.write(string)
    file.close

vsftpdconf()

def vsftpduser():
    with open('vsftpd.userlist', 'w') as file:
        file.write(share_user)
vsftpduser()
def sshfile():
    string=f"""
Include /etc/ssh/sshd_config.d/*.conf
AllowUsers {admin}
PermitRootLogin no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding yes
PrintMotd no
AcceptEnv LANG LC_*
Subsystem sftp	/usr/lib/openssh/sftp-server
PasswordAuthentication no
    """
    with open('sshd_config', 'w') as file:
        file.write(string)
sshfile()
def passfile():
    file = open('pass', 'w')
    file.writelines([share_password+'\n',share_password+'\n'])
    file.close()
passfile()
def smbfile():
    file = open('smb.conf', 'w')
    string = f"""
[global]
	encrypt passwords = yes
	server string = Serwer Samby
	workgroup = WORKGROUP
	netbios name = debian-1
	security = user
	name resolve order = bcast host
[folder]
	public = no
	browseable = yes
	writeable = yes
	path = /home/{share_user}
    """
    file.write(string)
    file.close()
smbfile()

def dockerfile():
    file = open('Dockerfile', 'w')

    docker_string = f"""
FROM debian:latest
RUN apt-get update -y
RUN apt-get install vsftpd samba openssh-server sudo -y
#EDIT this and pass file:
RUN useradd -m -p $(openssl passwd -6 {share_password}) {share_user}
RUN useradd -m -p $(openssl passwd -6 {admin_pass}) {admin}
RUN echo "{admin} ALL=(ALL:ALL) ALL" > /etc/sudoers
COPY pass /
RUN smbpasswd -a {share_user} -s < /pass
RUN rm -f /pass
RUN mkdir /home/{admin}/.ssh
COPY KEY.pub /home/{admin}/.ssh/authorized_keys
RUN chown -R {admin}:{admin} /home/{admin}
RUN chmod -R 700 /home/{admin}/.ssh/
RUN chmod 600 /home/{admin}/.ssh/authorized_keys
COPY sshd_config /etc/ssh/
COPY smb.conf /etc/samba/
COPY key /etc/
COPY vsftpd.conf /etc/vsftpd.conf
COPY vsftpd.userlist /etc/vsftpd.userlist
CMD service vsftpd start;service ssh start;service smbd start;bash
CMD chown -R {share_user}:{share_user} /home/{share_user};service vsftpd start;service ssh start;service smbd start;bash    
    """
    file.write(docker_string)
dockerfile()

#build and start docker
print('Building docker image')
name = input('Docker image name: ')
system(f'docker build -t {name} .')
print('OK')
