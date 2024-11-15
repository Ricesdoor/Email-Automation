from dotenv import load_dotenv
import imaplib
import email
import os
from bs4 import BeautifulSoup
import requests

load_dotenv()
username = os.getenv("EMAIL")
password = os.getenv("PASSWORD")

# função para se conectar ao e-mail
def connect_to_mail():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, password)
    mail.select("inbox")
    return mail

def extract_links_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    links = [link["href"] for link in soup.find_all("a", href=True) if "unsubscribe" in link["href"].lower()]
    return links

def click_link(link):
    try:
        response = requests.get(link)
        if response.status_code == 200:
            print("Link visitado com sucesso ", link)
        else:
            print("Falha ao visitar o link ", link, "error code", response.status_code)
    except Exception as e:
        print("Erro em ", link, str(e))


# função que procura por e-mails com a palavra "unsubscribe" em seu corpo
# a palavra pode ser alterada dependendo do idioma mais presente nos seus e-mails
def search_for_email():
    mail = connect_to_mail()
    _, search_data = mail.search(None, '(BODY "unsubscribe")')
    data = search_data[0].split()
    
    links = []

    # pede todo o conteúdo do e-mail 
    for num in data:
        _, data = mail.fetch(num, "(RFC822)")


        try:
            msg = email.message_from_bytes(data[0][1])
        except UnicodeDecodeError:
            print("Erro ao decodificar o e-mail em UTF-8. Tentando ISO-8859-1.")
            try:
                msg = email.message_from_bytes(data[0][1].decode('ISO-8859-1').encode('utf-8'))
            except Exception as e:
                print("Falha ao decodificar o e-mail:", str(e))
                continue


        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    try:
                        html_content = part.get_payload(decode=True).decode('utf-8')
                    except UnicodeDecodeError:
                        html_content = part.get_payload(decode=True).decode('ISO-8859-1')
                    links.extend(extract_links_from_html(html_content))
        else: 
            try:
                content = msg.get_payload(decode=True).decode('utf-8')
            except UnicodeDecodeError:
                content = msg.get_payload(decode=True).decode('ISO-8859-1')

            if msg.get_content_type() == "text/html":
                links.extend(extract_links_from_html(content))
                
    mail.logout()
    return links

def save_links(links):
    with open("links.txt", "w") as f:
        f.write("\n".join(links))

links = search_for_email()
for link in links:
    if link:
        click_link(link)

save_links(links)