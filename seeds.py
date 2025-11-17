# seeds.py

from datetime import datetime
from sqlalchemy.orm import Session

# importa engine / SessionLocal / Base
from database.database import SessionLocal, Base, engine

# importa os models (IMPORTANTE pra registrar as tabelas no Base)
from models.models import Usuario, Fabricante, Item, Transacao, TransacaoItem


def run_seeds(session: Session) -> None:
    # -------------------------
    # 1) Usuário "seed"
    # -------------------------
    usuario = Usuario(
        id=1,
        nome="Usuário Seed",
        email="seed@example.com",
        # Ajuste depois para um hash real, se necessário. Aqui é só p/ manter a FK.
        senha="senha123"
    )
    session.merge(usuario)

    # -------------------------
    # 2) Fabricantes
    # -------------------------
    fabricantes_data = [
        # 1
        {
            "id": 1,
            "razao_soc": "Samsung Electro-Mechanics Co., Ltd.",
            "endereco": "Suwon-si, Gyeonggi-do, Coreia do Sul",
            "pais_origem": "Coreia do Sul",
        },
        # 2
        {
            "id": 2,
            "razao_soc": "Murata Manufacturing Co., Ltd.",
            "endereco": "Nagaokakyo-shi, Kyoto, Japão",
            "pais_origem": "Japão",
        },
        # 3
        {
            "id": 3,
            "razao_soc": "TDK Corporation",
            "endereco": "Tóquio, Japão",
            "pais_origem": "Japão",
        },
        # 4
        {
            "id": 4,
            "razao_soc": "Würth Elektronik eiSos GmbH & Co. KG",
            "endereco": "Waldenburg, Alemanha",
            "pais_origem": "Alemanha",
        },
        # 5
        {
            "id": 5,
            "razao_soc": "NIC Components Corp.",
            "endereco": "Melville, NY, Estados Unidos",
            "pais_origem": "Estados Unidos",
        },
        # 6
        {
            "id": 6,
            "razao_soc": "Vishay Intertechnology, Inc.",
            "endereco": "Malvern, PA, Estados Unidos",
            "pais_origem": "Estados Unidos",
        },
        # 7
        {
            "id": 7,
            "razao_soc": "Panasonic Corporation",
            "endereco": "Kadoma, Osaka, Japão",
            "pais_origem": "Japão",
        },
        # 8
        {
            "id": 8,
            "razao_soc": "onsemi (ON Semiconductor Corporation)",
            "endereco": "Scottsdale, AZ, Estados Unidos",
            "pais_origem": "Estados Unidos",
        },
        # 9
        {
            "id": 9,
            "razao_soc": "Infineon Technologies AG",
            "endereco": "Neubiberg, região de Munique, Alemanha",
            "pais_origem": "Alemanha",
        },
        # 10
        {
            "id": 10,
            "razao_soc": "STMicroelectronics N.V.",
            "endereco": "Genebra, Suíça",
            "pais_origem": "Suíça",
        },
        # 11
        {
            "id": 11,
            "razao_soc": "ECS Inc. International",
            "endereco": "Olathe, Kansas, Estados Unidos",
            "pais_origem": "Estados Unidos",
        },
        # 12
        {
            "id": 12,
            "razao_soc": "Nichicon Corporation",
            "endereco": "Kyoto, Japão",
            "pais_origem": "Japão",
        },
        # 13
        {
            "id": 13,
            "razao_soc": "Yageo Corporation",
            "endereco": "Taipei, Taiwan",
            "pais_origem": "Taiwan",
        },
        # 14
        {
            "id": 14,
            "razao_soc": "Visual Communications Company, LLC (VCC)",
            "endereco": "San Marcos, CA, Estados Unidos",
            "pais_origem": "Estados Unidos",
        },
        # 15
        {
            "id": 15,
            "razao_soc": "Analog Devices, Inc.",
            "endereco": "Wilmington, MA, Estados Unidos",
            "pais_origem": "Estados Unidos",
        },
        # 16
        {
            "id": 16,
            "razao_soc": "Amphenol RF / Amphenol Corporation",
            "endereco": "Wallingford, CT, Estados Unidos",
            "pais_origem": "Estados Unidos",
        },
        # 17
        {
            "id": 17,
            "razao_soc": "Semitec Corporation",
            "endereco": "Tóquio, Japão",
            "pais_origem": "Japão",
        },
        # 18
        {
            "id": 18,
            "razao_soc": "Littelfuse, Inc.",
            "endereco": "Chicago, IL, Estados Unidos",
            "pais_origem": "Estados Unidos",
        },
        # 19
        {
            "id": 19,
            "razao_soc": "Mobile Mark, Inc.",
            "endereco": "Itasca, IL, Estados Unidos",
            "pais_origem": "Estados Unidos",
        },
        # 20
        {
            "id": 20,
            "razao_soc": "Meritek Electronics Corporation",
            "endereco": "New Taipei City, Taiwan",
            "pais_origem": "Taiwan",
        },
        # 21
        {
            "id": 21,
            "razao_soc": "Dialight plc",
            "endereco": "Londres, Reino Unido",
            "pais_origem": "Reino Unido",
        },
        # 22
        {
            "id": 22,
            "razao_soc": "Olimex Ltd.",
            "endereco": "Plovdiv, Bulgária",
            "pais_origem": "Bulgária",
        },
    ]

    for fab in fabricantes_data:
        session.merge(Fabricante(**fab))

    # -------------------------
    # 3) Itens (TODOS os partnumbers dos 3 PDFs)
    # -------------------------
    itens_data = [
        # -------- AVNET --------
        {
            "partnumber": "CL10C330JB8NNNC",
            "ncm": "85322410",
            "descricao": "CAP.CER.SMD 0603 33PF 50V 5% C0G",
            "descricao_curta": "Capacitor cerâmico 33pF 50V 0603 C0G",
            "fabricante_id": 1,  # Samsung EM
        },
        {
            "partnumber": "CL10B472KB8NNNC",
            "ncm": "85322410",
            "descricao": "CAP.CER.SMD 0603 4.7NF 50V 10% X7R",
            "descricao_curta": "Capacitor cerâmico 4,7nF 50V 0603 X7R",
            "fabricante_id": 1,
        },
        {
            "partnumber": "GRM1885C1H180JA01D",
            "ncm": "85322410",
            "descricao": "CAP.CER.SMD 0603 18PF 50V 5% NP0",
            "descricao_curta": "Capacitor cerâmico 18pF 50V 0603 NP0",
            "fabricante_id": 2,  # Murata
        },
        {
            "partnumber": "CL10A106KP8NNNC",
            "ncm": "85322410",
            "descricao": "CAP.CER.SMD 0603 10UF 10V 10% X5R",
            "descricao_curta": "Capacitor cerâmico 10µF 10V 0603 X5R",
            "fabricante_id": 1,
        },
        {
            "partnumber": "C1608X5R1E106M080AC",
            "ncm": "85322410",
            "descricao": "CAP.CER.SMD 0603 10UF 25V 20% X5R",
            "descricao_curta": "Capacitor cerâmico 10µF 25V 0603 X5R",
            "fabricante_id": 3,  # TDK
        },
        {
            "partnumber": "88512006119",
            "ncm": "85322410",
            "descricao": "CAP.CER.SMD 0603 10NF 100V 10% X7R",
            "descricao_curta": "Capacitor cerâmico 10nF 100V 0603 X7R",
            "fabricante_id": 4,  # Würth
        },
        {
            "partnumber": "NACE100M100V6.3X8TR13F",
            "ncm": "85322200",
            "descricao": "CAP.ALU.SMD 10UF 100V 20%",
            "descricao_curta": "Capacitor eletrolítico alumínio 10µF 100V SMD",
            "fabricante_id": 5,  # NIC Components
        },
        {
            "partnumber": "CRCW060320K0FKEA",
            "ncm": "85332120",
            "descricao": "RES.SMD 0603 20K0 1%",
            "descricao_curta": "Resistor SMD 0603 20kΩ 1%",
            "fabricante_id": 6,  # Vishay
        },
        {
            "partnumber": "ERJ-2RKF2201X",
            "ncm": "85332120",
            "descricao": "RES.SMD 0402 2K20 1%",
            "descricao_curta": "Resistor SMD 0402 2,2kΩ 1%",
            "fabricante_id": 7,  # Panasonic
        },
        {
            "partnumber": "BC847BLT1G",
            "ncm": "85412120",
            "descricao": "BC847B NPN TRANSISTOR 45V 100MA SOT-23",
            "descricao_curta": "Transistor NPN BC847B 45V 100mA SOT-23",
            "fabricante_id": 8,  # onsemi
        },
        {
            "partnumber": "IRLML6401TRPBF",
            "ncm": "85412999",
            "descricao": "MOSFET P-CH 12V 3.7A SOT-23",
            "descricao_curta": "MOSFET P-channel 12V 3,7A SOT-23",
            "fabricante_id": 9,  # Infineon
        },
        {
            "partnumber": "STPS5H100B-TR",
            "ncm": "85411011",
            "descricao": "DIODE SCHOTTKY 5A 100V TO-252AA",
            "descricao_curta": "Diodo Schottky 5A 100V DPAK",
            "fabricante_id": 10,  # ST
        },
        {
            "partnumber": "ESD7C3.3DT5G",
            "ncm": "85411029",
            "descricao": "DIODE ESD UNI 3.3V SOT-23",
            "descricao_curta": "Diodo proteção ESD 3,3V SOT-23",
            "fabricante_id": 8,  # onsemi
        },
        {
            "partnumber": "LD1117ADT-TR",
            "ncm": "85423990",
            "descricao": "VOLT REG LDO 5V 800MA DPAK",
            "descricao_curta": "Regulador LDO 5V 800mA DPAK",
            "fabricante_id": 10,  # ST
        },
        {
            "partnumber": "ECS-3225Q-33-260-BS-TR",
            "ncm": "85416090",
            "descricao": "OSC.SMD 26MHZ 3.3V 11PFC",
            "descricao_curta": "Oscilador SMD 26MHz 3,3V 3,2x2,5mm",
            "fabricante_id": 11,  # ECS
        },

        # -------- MOUSER --------
        {
            "partnumber": "B32932A3224K189",
            "ncm": "85322590",
            "descricao": "Capacitor X2 .22µF 305VAC AEC-Q200",
            "descricao_curta": "Capacitor filme X2 0,22µF 305VAC",
            "fabricante_id": 3,  # TDK / EPCOS
        },
        {
            "partnumber": "EEU-FM1E152B",
            "ncm": "85322200",
            "descricao": "Capacitor eletrolítico alumínio 1500µF 25V série FM",
            "descricao_curta": "Capacitor eletrolítico 1500µF 25V radial",
            "fabricante_id": 7,  # Panasonic
        },
        {
            "partnumber": "LLG2G151MELZ25",
            "ncm": "85322200",
            "descricao": "Capacitor eletrolítico alumínio 150µF 400V snap-in",
            "descricao_curta": "Capacitor eletrolítico 150µF 400V snap-in",
            "fabricante_id": 12,  # Nichicon
        },
        {
            "partnumber": "RC0603FR-077K5L",
            "ncm": "85332120",
            "descricao": "Resistor SMD 0603 7.5kΩ 1%",
            "descricao_curta": "Resistor 0603 7,5kΩ 1%",
            "fabricante_id": 13,  # Yageo
        },
        {
            "partnumber": "RC0805JR-0733KL",
            "ncm": "85332120",
            "descricao": "Resistor SMD 0805 33kΩ 5%",
            "descricao_curta": "Resistor 0805 33kΩ 5%",
            "fabricante_id": 13,  # Yageo
        },
        {
            "partnumber": "STTH102AY",
            "ncm": "85411011",
            "descricao": "Diodo ultrarrápido 1A 200V axial",
            "descricao_curta": "Diodo retificador rápido 1A 200V",
            "fabricante_id": 10,  # ST
        },
        {
            "partnumber": "LFC075CTP",
            "ncm": "85319090",  # estimado pela natureza do produto (indicador/luz flexível)
            "descricao": "LED indicador flexível - LFC075 série",
            "descricao_curta": "LED flexível LFC075",
            "fabricante_id": 14,  # VCC
        },
        {
            "partnumber": "LTC3625EDE#PBF",
            "ncm": "85423990",
            "descricao": "LTC3625 - Carregador de supercapacitor 2 células, síncrono",
            "descricao_curta": "CI regulador/carregador LTC3625",
            "fabricante_id": 15,  # Analog Devices
        },
        {
            "partnumber": "132119",
            "ncm": "85366990",
            "descricao": "Conector RF, BNC Jack to UHF Plug Adapter",
            "descricao_curta": "Adaptador RF 132119",
            "fabricante_id": 16,  # Amphenol RF
        },
        {
            "partnumber": "132119RP",
            "ncm": "85366990",
            "descricao": "Conector RF, BNC Jack to UHF Plug Adapter (Reverse Polarity)",
            "descricao_curta": "Adaptador RF 132119RP",
            "fabricante_id": 16,
        },
        {
            "partnumber": "691351500005",
            "ncm": "85366990",
            "descricao": "Bornes plugáveis 5 vias 5,08mm WR-TBL",
            "descricao_curta": "Terminal block plugável 5 vias",
            "fabricante_id": 4,  # Würth
        },
        {
            "partnumber": "8D2-11LCS",
            "ncm": "85334011",
            "descricao": "Sensor de temperatura NTC 8D2-11LCS",
            "descricao_curta": "NTC termistor 8D2-11LCS",
            "fabricante_id": 17,  # Semitec
        },
        {
            "partnumber": "AHEF1000",
            "ncm": "85332900",
            "descricao": "Fusível térmico/limitador AHEF1000",
            "descricao_curta": "Dispositivo de proteção resetável AHEF1000",
            "fabricante_id": 18,  # Littelfuse
        },

        # -------- XWORKS --------
        {
            "partnumber": "74406042010",
            "ncm": "85045000",
            "descricao": "Indutor SMD WE-LQFS 1µH 4,47A blindado",
            "descricao_curta": "Indutor SMD 1µH 4,47A",
            "fabricante_id": 4,  # Würth
        },
        {
            "partnumber": "MGRM-WLF-3C-BLK-120",
            "ncm": "85177900",
            "descricao": "Antena mag-mount LTE/WiFi MGRM-WLF-3C-BLK-120",
            "descricao_curta": "Antena magnética LTE/WiFi 3dBi",
            "fabricante_id": 19,  # Mobile Mark
        },
        {
            "partnumber": "614004134726",
            "ncm": "85366940",
            "descricao": "Conector USB-A fêmea 4P direito, WR-COM",
            "descricao_curta": "Conector USB-A 2.0 4 vias",
            "fabricante_id": 4,  # Würth
        },
        {
            "partnumber": "691313510002",
            "ncm": "85366940",
            "descricao": "Header PCB bornes plugáveis WR-TBL 2P 5,08mm",
            "descricao_curta": "Header 2 pinos WR-TBL 5,08mm",
            "fabricante_id": 4,  # Würth
        },
        {
            "partnumber": "691351500002",
            "ncm": "85369040",
            "descricao": "Plug bornes plugáveis WR-TBL 2P 5,08mm",
            "descricao_curta": "Terminal block plug 2 vias 5,08mm",
            "fabricante_id": 4,  # Würth
        },
        {
            "partnumber": "MA0603CG150J500",
            "ncm": "85322400",
            "descricao": "CAP CER 15PF 50V C0G/NP0 0603",
            "descricao_curta": "Capacitor cerâmico 15pF 50V 0603 C0G",
            "fabricante_id": 20,  # Meritek
        },
        {
            "partnumber": "597-2311-407F",
            "ncm": "85414100",
            "descricao": "LED verde SMD 1208 right-angle",
            "descricao_curta": "LED verde 1208 597-2311-407F",
            "fabricante_id": 21,  # Dialight
        },
        {
            "partnumber": "597-2401-407F",
            "ncm": "85414020",
            "descricao": "LED amarelo SMD 1208 right-angle",
            "descricao_curta": "LED amarelo 1208 597-2401-407F",
            "fabricante_id": 21,  # Dialight
        },
        {
            "partnumber": "IMX233-OLINUXINO-MAXI",
            "ncm": "85371090",
            "descricao": "Placa de desenvolvimento IMX233-OLINUXINO-MAXI",
            "descricao_curta": "Single-board computer i.MX233 Olinuxino Maxi",
            "fabricante_id": 22,  # Olimex
        },
    ]

    for item in itens_data:
        session.merge(Item(**item))

    # -------------------------
    # 4) Transações (1 por PDF)
    # -------------------------
    transacoes_data = [
        {
            "id": 1,
            "nome": "AVNET - Pedido 06/02/2025",
            "usuario_id": 1,
        },
        {
            "id": 2,
            "nome": "MOUSER - Fatura 69KV E FONTE TPS118",
            "usuario_id": 1,
        },
        {
            "id": 3,
            "nome": "XWORKS - Invoice 03/05/2025",
            "usuario_id": 1,
        },
    ]

    for t in transacoes_data:
        session.merge(Transacao(**t))

    # -------------------------
    # 5) TransacaoItem
    # -------------------------
    transacao_itens_data = [
        # ----- AVNET (Transacao 1) -----
        {"transacao_id": 1, "item_partnumber": "CL10C330JB8NNNC", "quantidade": 4000, "preco_extraido": 0.0045},
        {"transacao_id": 1, "item_partnumber": "CL10B472KB8NNNC", "quantidade": 8000, "preco_extraido": 0.0028},
        {"transacao_id": 1, "item_partnumber": "GRM1885C1H180JA01D", "quantidade": 4000, "preco_extraido": 0.0121},
        {"transacao_id": 1, "item_partnumber": "CL10A106KP8NNNC", "quantidade": 8000, "preco_extraido": 0.0121},
        {"transacao_id": 1, "item_partnumber": "C1608X5R1E106M080AC", "quantidade": 4000, "preco_extraido": 0.0781},
        {"transacao_id": 1, "item_partnumber": "88512006119", "quantidade": 10000, "preco_extraido": 0.0148},
        {"transacao_id": 1, "item_partnumber": "NACE100M100V6.3X8TR13F", "quantidade": 4000, "preco_extraido": 0.5546},
        {"transacao_id": 1, "item_partnumber": "CRCW060320K0FKEA", "quantidade": 5000, "preco_extraido": 0.0099},
        {"transacao_id": 1, "item_partnumber": "ERJ-2RKF2201X", "quantidade": 5000, "preco_extraido": 0.0136},
        {"transacao_id": 1, "item_partnumber": "BC847BLT1G", "quantidade": 5000, "preco_extraido": 0.0453},
        {"transacao_id": 1, "item_partnumber": "IRLML6401TRPBF", "quantidade": 5000, "preco_extraido": 0.1383},
        {"transacao_id": 1, "item_partnumber": "STPS5H100B-TR", "quantidade": 2000, "preco_extraido": 0.6480},
        {"transacao_id": 1, "item_partnumber": "ESD7C3.3DT5G", "quantidade": 4000, "preco_extraido": 0.0949},
        {"transacao_id": 1, "item_partnumber": "LD1117ADT-TR", "quantidade": 2000, "preco_extraido": 0.3979},
        {"transacao_id": 1, "item_partnumber": "ECS-3225Q-33-260-BS-TR", "quantidade": 3000, "preco_extraido": 0.8274},

        # ----- MOUSER (Transacao 2) -----
        {"transacao_id": 2, "item_partnumber": "B32932A3224K189", "quantidade": 100, "preco_extraido": None},
        {"transacao_id": 2, "item_partnumber": "EEU-FM1E152B", "quantidade": 500, "preco_extraido": None},
        {"transacao_id": 2, "item_partnumber": "LLG2G151MELZ25", "quantidade": 50, "preco_extraido": None},
        {"transacao_id": 2, "item_partnumber": "RC0603FR-077K5L", "quantidade": 1000, "preco_extraido": None},
        {"transacao_id": 2, "item_partnumber": "RC0805JR-0733KL", "quantidade": 1000, "preco_extraido": None},
        {"transacao_id": 2, "item_partnumber": "STTH102AY", "quantidade": 500, "preco_extraido": None},
        {"transacao_id": 2, "item_partnumber": "LFC075CTP", "quantidade": 25, "preco_extraido": None},
        {"transacao_id": 2, "item_partnumber": "LTC3625EDE#PBF", "quantidade": 25, "preco_extraido": None},
        {"transacao_id": 2, "item_partnumber": "132119", "quantidade": 25, "preco_extraido": None},
        {"transacao_id": 2, "item_partnumber": "132119RP", "quantidade": 25, "preco_extraido": None},
        {"transacao_id": 2, "item_partnumber": "691351500005", "quantidade": 25, "preco_extraido": None},
        {"transacao_id": 2, "item_partnumber": "8D2-11LCS", "quantidade": 100, "preco_extraido": None},
        {"transacao_id": 2, "item_partnumber": "AHEF1000", "quantidade": 100, "preco_extraido": None},

        # ----- XWORKS (Transacao 3) -----
        {"transacao_id": 3, "item_partnumber": "74406042010", "quantidade": 1, "preco_extraido": None},
        {"transacao_id": 3, "item_partnumber": "MGRM-WLF-3C-BLK-120", "quantidade": 1, "preco_extraido": None},
        {"transacao_id": 3, "item_partnumber": "614004134726", "quantidade": 1, "preco_extraido": None},
        {"transacao_id": 3, "item_partnumber": "691313510002", "quantidade": 1, "preco_extraido": None},
        {"transacao_id": 3, "item_partnumber": "691351500002", "quantidade": 1, "preco_extraido": None},
        {"transacao_id": 3, "item_partnumber": "MA0603CG150J500", "quantidade": 1, "preco_extraido": None},
        {"transacao_id": 3, "item_partnumber": "597-2311-407F", "quantidade": 1, "preco_extraido": None},
        {"transacao_id": 3, "item_partnumber": "597-2401-407F", "quantidade": 1, "preco_extraido": None},
        {"transacao_id": 3, "item_partnumber": "IMX233-OLINUXINO-MAXI", "quantidade": 1, "preco_extraido": None},
    ]

    for ti in transacao_itens_data:
        session.add(TransacaoItem(**ti))

    session.commit()
    print("Seeds inseridos com sucesso.")


if __name__ == "__main__":
    # 1) garante que as tabelas existem (caso ainda não tenha rodado nada que crie)
    Base.metadata.create_all(bind=engine)

    # 2) abre sessão e roda o seed
    db = SessionLocal()
    try:
        run_seeds(db)
    finally:
        db.close()
