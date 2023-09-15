from sqlalchemy import Column
from sqlalchemy import create_engine, func, select, and_
from sqlalchemy.dialects.sqlite import (INTEGER, VARCHAR, DATETIME, FLOAT)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from config import parameters
from seguranca.business_exception import BusinessException
from seguranca.pemissoes import Permissao

from paciente import Paciente
from hospital import Hospital
from datetime import datetime, timedelta 
from calendar import monthrange
from flask import jsonify

Base = declarative_base()

# Mapeia o banco de dados
engine = create_engine(parameters['SQLALCHEMY_DATABASE_URI'], echo=True)
session = Session(engine)

class Agendamento(Base):
    # Identifica a tabela no Banco de Dados
    __tablename__ = "AGENDAMENTO"
    
    # Propriedades da Classe
    agendamento_id = Column(INTEGER, primary_key=True)
    paciente_id = Column(INTEGER)
    tipo_encaminhamento_id = Column(INTEGER)
    tipo_doenca_id = Column(INTEGER)
    tipo_remocao_id = Column(INTEGER)
    hospital_id = Column(INTEGER)
    veiculo_id = Column(INTEGER)
    usuario_id = Column(INTEGER)
    motorista_id = Column(INTEGER)
    responsavel_pac = Column(VARCHAR(250))
    data_remocao = Column(DATETIME)
    saida_prevista = Column(DATETIME)
    observacao = Column(VARCHAR(250))
    custo_ifd = Column(FLOAT)
    custo_estadia = Column(FLOAT)

    # Método de Representação
    def __repr__(self) -> str:
        return f"Agendamento(agendamento_id={self.agendamento_id!r},paciente_id={self.paciente_id!r}, tipo_encaminhamento_id={self.tipo_encaminhamento_id!r}\
            tipo_doenca_id={self.tipo_doenca_id!r},tipo_remocao_id={self.tipo_remocao_id!r}, hospital_id={self.hospital_id!r}, veiculo_id={self.veiculo_id!r}\
            usuario_id={self.usuario_id!r},motorista_id={self.motorista_id!r}, responsavel_pac={self.responsavel_pac!r}, data_remocao={self.data_remocao!r}\
            saida_prevista={self.saida_prevista!r},observacao={self.observacao!r}, custo_ifd={self.custo_ifd!r}, custo_estadia={self.custo_estadia!r}\
            )"

    # Método de Inicialização
    def __init__(self, agendamento_id, paciente_id, tipo_encaminhamento_id, tipo_doenca_id, tipo_remocao_id, hospital_id, veiculo_id, usuario_id, motorista_id,\
        responsavel_pac, data_remocao, saida_prevista, observacao, custo_ifd, custo_estadia ):
        self.agendamento_id = agendamento_id
        self.paciente_id = paciente_id
        self.tipo_encaminhamento_id = tipo_encaminhamento_id
        self.tipo_doenca_id = tipo_doenca_id
        self.tipo_remocao_id = tipo_remocao_id
        self.hospital_id = hospital_id
        self.veiculo_id = veiculo_id
        self.usuario_id = usuario_id
        self.motorista_id = motorista_id
        self.responsavel_pac = responsavel_pac
        self.data_remocao = data_remocao
        self.saida_prevista = saida_prevista
        self.observacao = observacao
        self.custo_ifd = custo_ifd
        self.custo_estadia = custo_estadia

    # Retorna o resultado da Classe em formato json
    def obj_to_dict(self):
        return {
            "agendamento_id": int(self.agendamento_id),
            "paciente_id": int(self.paciente_id),
            "tipo_encaminhamento_id": int(self.tipo_encaminhamento_id),
            "tipo_doenca_id": int(self.tipo_doenca_id),
            "tipo_remocao_id": int(self.tipo_remocao_id),
            "hospital_id": int(self.hospital_id),
            "veiculo_id": int(self.veiculo_id),
            "motorista_id": int(self.motorista_id),
            "responsavel_pac": self.responsavel_pac,
            "data_remocao": str(self.data_remocao),
            "data_remocao": str(self.saida_prevista),            
            "observacao": self.observacao,
            "custo_ifd": self.custo_ifd,
            "custo_estadia": self.custo_estadia
        }

    # Retorna o total de pacientes cadastrados no sistema
    def get_total_agendamento(usuario_id):
        # Verifica se o usuário pode ver o conteúdo da tabela hospital
        acesso_liberado = Permissao.valida_permissao_usuario(usuario_id, 'Pode_Visualizar_Hospitais')
        if not acesso_liberado:
            return 0
        else:
            total = session.query(func.count(Agendamento.agendamento_id)).scalar()
            return total
    
    def get_last_agendamentos(usuario_id):        
        listAgendamentos = []
        # Verifica se o usuário pode ver o conteúdo da tabela hospital
        acesso_liberado = Permissao.valida_permissao_usuario(usuario_id, 'Pode_Visualizar_Hospitais')
        if not acesso_liberado:
            return listAgendamentos
        else:           
            agendamentos = session.query(Agendamento, Paciente, Hospital )\
                .join(Paciente, Agendamento.paciente_id == Paciente.paciente_id)\
                .join(Hospital, Agendamento.hospital_id == Hospital.hospital_id)\
                .order_by(Agendamento.agendamento_id.desc()).limit(10).all()
            
            for agendamento in agendamentos:
                ag =  {
                    "agendamento_id": agendamento.Agendamento.agendamento_id,
                    "nome": agendamento.Paciente.nome,
                    "data_nascimento": datetime.isoformat(agendamento.Paciente.data_nasc),
                    "data_remocao": datetime.isoformat(agendamento.Agendamento.data_remocao),
                    "hospital": agendamento.Hospital.nome
                }   
                listAgendamentos.append(ag)   

        return listAgendamentos

    def get_agendamentos_ano(usuario_id):        
        acesso_liberado = Permissao.valida_permissao_usuario(usuario_id, 'Pode_Visualizar_Hospitais')
        if not acesso_liberado:
            return None
        else: 
            atendimentos_mes = []
            hoje = datetime.today()
            ano = hoje.year
            inicio_ano = hoje.replace(day=1, month=1, year=ano, hour=0, minute=0, second=1 )
            fim_ano = hoje.replace(day=31, month=12, year=ano, hour=23, minute=59, second=59)            
            total = session.query(func.strftime("%m", Agendamento.data_remocao), func.count(func.strftime("%m", Agendamento.data_remocao)))\
                .filter(Agendamento.data_remocao.between(inicio_ano, fim_ano))\
                .group_by(func.strftime("%m", Agendamento.data_remocao), func.strftime("%m", Agendamento.data_remocao)).all()
            
            for i in range(1,13):
                y = ''
                if i < 10:
                    y = f'0{i}'
                else:
                    y = str(i)
                
                #at = {f'{y}' : 0}
                at = 0
                
                for mes in total:
                  
                    if mes[0] == y:
                        #at = {f'{y}' : mes[1]}
                        at = mes[1]
                        
                atendimentos_mes.append(at)
        
        return atendimentos_mes
     