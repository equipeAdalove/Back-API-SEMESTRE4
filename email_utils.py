import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from pathlib import Path

conf = ConnectionConfig(
    MAIL_USERNAME="adatech04@gmail.com",    # Coloque seu e-mail aqui
    MAIL_PASSWORD="hevhceqfzcygerij",     # Coloque sua senha de aplicativo aqui
    MAIL_FROM="adatech04@gmail.com",      # Quem está enviando
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# 2. FUNÇÃO DE ENVIO (COM O LAYOUT BONITO)
async def send_welcome_email(email_to: EmailStr, name: str):
    # Definindo cores baseadas no conceito 'Tech'
    primary_color = "#2B4C7E"
    bg_color = "#F4F4F7"
    
    # Garante que o caminho para a pasta static esteja correto
    # Ajuste "static" se sua pasta tiver outro nome ou caminho
    base_dir = Path(__file__).resolve().parent
    logo_path = base_dir / "static" / "rodape.jpeg" # Certifique-se que o arquivo NÃO tem acento

    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin: 0; padding: 0; background-color: {bg_color}; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        
        <div style="width: 100%; background-color: {bg_color}; padding: 40px 0;">
            
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                
                <div style="padding: 40px 40px 20px 40px;">
                    <h2 style="color: {primary_color}; margin-top: 0; font-size: 24px;">Olá, {name}!</h2>
                    
                    <p style="color: #555; font-size: 16px; line-height: 1.6;">
                        Seja muito bem-vindo(a) à <strong>AdaTech</strong>. É um prazer ter você conosco.
                    </p>

                    <p style="color: #555; font-size: 16px; line-height: 1.6;">
                        Seu cadastro foi concluído com sucesso. A partir de agora, você tem em mãos uma solução 
                        desenvolvida para elevar a eficiência e a segurança do seu registro aduaneiro.
                    </p>

                    <div style="background-color: #F8F9FA; border-left: 4px solid {primary_color}; padding: 20px; margin: 25px 0; border-radius: 4px;">
                        <p style="margin: 0; color: #333; font-size: 15px; line-height: 1.6;">
                            <strong>O que a AdaTech faz por você:</strong><br><br>
                            Nossa plataforma automatiza a criação da instrução de registro, integrando inteligentemente:
                        </p>
                        <ul style="margin: 10px 0 0 0; padding-left: 20px; color: #555;">
                            <li>Part-Number e Classificação Fiscal</li>
                            <li>Dados do Fabricante</li>
                            <li>Origem da mercadoria</li>
                        </ul>
                    </div>

                    <p style="color: #555; font-size: 16px; line-height: 1.6;">
                        Nosso objetivo é gerar descrições completas e compatíveis com as exigências legais.
                    </p>

                    <p style="margin-top: 30px; color: #333; font-weight: bold;">
                        Atenciosamente,<br>
                        <span style="color: {primary_color};">Equipe Adalove</span>
                    </p>
                </div>

                <div style="width: 100%; margin-top: 10px;">
                    <img src="cid:rodape" alt="AdaTech Footer" style="width: 100%; display: block; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;" />
                </div>
            
            </div>
            
            <div style="text-align: center; padding-top: 20px; color: #999; font-size: 12px;">
                &copy; 2025 Adalove. Todos os direitos reservados.
            </div>

        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Bem-vindo(a) à AdaTech!",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
        attachments=[
            {
                "file": str(logo_path), 
                "headers": {
                    "Content-ID": "<rodape>",
                    "Content-Disposition": "inline"  
                },
                "mime_type": "image",     # <--- (Boa prática)
                "mime_subtype": "jpeg"  
            }
        ]
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
    except Exception as e:
        print(f"Erro ao tentar enviar o email: {e}")
        # É uma boa ideia logar esse erro em um arquivo


async def send_recovery_email(email_to: EmailStr, code: str):
    """
    Envia um email estilizado com o código de recuperação.
    """
    # Configurações de Estilo (Mantendo a identidade da AdaTech)
    primary_color = "#2B4C7E"
    secondary_color = "#E8F0FE" # Um azul bem clarinho para fundo de destaque
    bg_color = "#F4F4F7"
    text_color = "#333333"

    # Caminho da imagem (O mesmo da função de Welcome)
    base_dir = Path(__file__).resolve().parent
    logo_path = base_dir / "static" / "rodape.jpeg"

    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin: 0; padding: 0; background-color: {bg_color}; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        
        <div style="width: 100%; background-color: {bg_color}; padding: 40px 0;">
            
            <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                
                <div style="background-color: {primary_color}; height: 8px; width: 100%;"></div>

                <div style="padding: 40px 40px 30px 40px; text-align: center;">
                    
                    <div style="font-size: 40px; margin-bottom: 10px;">🔒</div>

                    <h2 style="color: {primary_color}; margin-top: 0; margin-bottom: 10px; font-size: 24px;">
                        Recuperação de Senha
                    </h2>
                    
                    <p style="color: #666; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
                        Recebemos uma solicitação para redefinir a senha da sua conta <strong>AdaTech</strong>.
                    </p>
                    
                    <div style="background-color: {secondary_color}; border: 1px dashed {primary_color}; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <p style="margin: 0; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: {primary_color}; font-weight: bold;">
                            Seu código de verificação
                        </p>
                        <p style="margin: 10px 0 0 0; font-size: 36px; letter-spacing: 8px; font-weight: bold; color: #333; font-family: 'Courier New', monospace;">
                            {code}
                        </p>
                    </div>

                    <p style="color: #888; font-size: 14px; margin-top: 25px;">
                        Este código é válido por <strong>15 minutos</strong>.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">

                    <p style="color: #999; font-size: 12px; line-height: 1.4;">
                        Se você não solicitou essa alteração, por favor ignore este e-mail ou entre em contato com o suporte. Nenhuma alteração foi feita em sua conta.
                    </p>
                </div>

                <div style="width: 100%;">
                    <img src="cid:rodape" alt="AdaTech Footer" style="width: 100%; display: block;" />
                </div>
            
            </div>
            
            <div style="text-align: center; padding-top: 20px; color: #999; font-size: 12px;">
                &copy; 2025 Adalove. Segurança em primeiro lugar.
            </div>

        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="AdaTech - Código de Recuperação",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
        # IMPORTANTE: Adicionei os anexos aqui também para a imagem funcionar
        attachments=[
            {
                "file": str(logo_path), 
                "headers": {
                    "Content-ID": "<rodape>",
                    "Content-Disposition": "inline"  
                },
                "mime_type": "image",
                "mime_subtype": "jpeg"  
            }
        ]
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
    except Exception as e:
        print(f"Erro ao enviar email de recuperação: {e}")