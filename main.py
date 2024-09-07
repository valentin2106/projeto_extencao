import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import configparser

def gerar_relatorio_atendimento_gratuito(caminho_planilha_fisioterapia, caminho_planilha_clinica, valor_por_paciente_gratis=5000):
    df_fisioterapia = pd.read_excel(caminho_planilha_fisioterapia)
    df_clinica = pd.read_excel(caminho_planilha_clinica)
    
    df_fisioterapia['Valor do Atendimento'] = df_fisioterapia['Valor do Atendimento'].replace({'R\$ ': '', ',': ''}, regex=True).astype(float)
    
    faturamento_acumulado = 0
    pacientes_gratuitos = []
    indice_paciente_clinica = 0
    
    for i, row in df_fisioterapia.iterrows():
        faturamento_acumulado += row['Valor do Atendimento']
        
        if faturamento_acumulado >= valor_por_paciente_gratis and indice_paciente_clinica < len(df_clinica):
            paciente_gratuito = df_clinica.iloc[indice_paciente_clinica]
            
            pacientes_gratuitos.append({
                'Nome do Paciente Gratuito': paciente_gratuito['Nome do Paciente'],
                'Endereço': paciente_gratuito['Endereço'],
                'Renda Mensal (R$)': paciente_gratuito['Renda Mensal (R$)'],
                'Valor Acumulado': faturamento_acumulado
            })
            
            faturamento_acumulado = 0
            
            indice_paciente_clinica += 1
    
    df_relatorio = pd.DataFrame(pacientes_gratuitos)
    
    return df_relatorio

def enviar_email_com_anexo(destinatario, destinatario2, assunto, corpo_email, caminho_anexo):
    config = configparser.ConfigParser()
    config.read('config.ini')

    remetente = config.get('email', 'remetente')
    senha = config.get('email', 'senha')
    smtp_server = config.get('email', 'smtp_server')
    smtp_port = config.getint('email', 'smtp_port')

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['To'] = destinatario2
    msg['Subject'] = assunto

    msg.attach(MIMEText(corpo_email, 'plain'))

    with open(caminho_anexo, 'rb') as anexo:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(anexo.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(caminho_anexo)}')
        msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(remetente, senha)
        text = msg.as_string()
        server.sendmail(remetente, destinatario, text)
        server.quit()
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Falha ao enviar e-mail: {str(e)}")

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')

    caminho_planilha_fisioterapia = config.get('paths', 'caminho_planilha_fisioterapia')
    caminho_planilha_clinica = config.get('paths', 'caminho_planilha_clinica')
    caminho_relatorio = config.get('paths', 'caminho_relatorio')
    destinatario = config.get('paths', 'destinatario')
    destinatario2 = config.get('paths', 'destinatario2')
    
    relatorio = gerar_relatorio_atendimento_gratuito(caminho_planilha_fisioterapia, caminho_planilha_clinica)
    
    relatorio.to_excel(caminho_relatorio, index=False)
    
    assunto = 'Relatório de Pacientes Atendidos Gratuitamente'
    corpo_email = 'Segue em anexo o relatório de pacientes que receberam atendimento gratuito.'
    
    enviar_email_com_anexo(destinatario, destinatario2, assunto, corpo_email, caminho_relatorio)
