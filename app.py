import os
import json
import gradio as gr
import psycopg2
import re
from urllib.parse import urlparse

import os
import psycopg2
from urllib.parse import urlparse

def criar_conexao():
    DATABASE_URL = os.getenv('HEROKU_POSTGRESQL_RED_URL')
    url = urlparse(DATABASE_URL)
    try:
        port = int(url.port) if url.port else 5432
    except ValueError:
        port = 5432

    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=port
    )
    return conn

def criar_tabela(conn):
    try:
        with conn.cursor() as cur:
            cur.execute(''' 
                CREATE TABLE IF NOT EXISTS dados_lipedema (
                    id SERIAL PRIMARY KEY,
                    nome_completo VARCHAR(255),
                    email VARCHAR(255),
                    idade INTEGER,
                    peso FLOAT,
                    profissao VARCHAR(255),
                    whatsapp VARCHAR(20),
                    pontuacao INTEGER,
                    resultado VARCHAR(255)
                )
            ''')
            conn.commit()
            print("Tabela criada ou já existente.")
    except Exception as e:
        print(f"Erro ao criar a tabela: {e}")

def verificar_tabelas(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        tabelas = cur.fetchall()
        print("Tabelas existentes:", tabelas)

if __name__ == '__main__':
    try:
        conn = criar_conexao()
        print("Conexão estabelecida com sucesso!")
        verificar_tabelas(conn)
        criar_tabela(conn)
        conn.close()
    except Exception as e:
        print(f"Erro geral: {e}")

# Função para processar o formulário e gerar o resultado
def processar_formulario(nome, email, idade, peso, profissao, whatsapp, *respostas):
    # Criar a conexão com o banco de dados
    conn = criar_conexao()

    # Validar campos obrigatórios
    if not nome or not email or not idade or not peso or not profissao or not whatsapp:
        conn.close()
        return "Por favor, preencha todas as informações pessoais."

    # Calcular pontuação
    pontuacao = 0
    for i, resposta in enumerate(respostas):
        option_index = questions[i][1].index(resposta)
        pontuacao += questions[i][2][option_index]

    # Definir o resultado com base na pontuação
    if pontuacao >= 13:
        resultado = "75-100% de chance de ter lipedema"
        orientacao = "Os sintomas indicam uma alta probabilidade de lipedema, sugerindo a necessidade de atenção especializada para uma melhor compreensão e tratamento da condição."
    elif pontuacao >= 9:
        resultado = "50-75% de chance de ter lipedema"
        orientacao = "Os sinais apontam para uma chance moderada de lipedema, o que pode justificar uma análise cuidadosa dos sintomas para confirmação e possíveis orientações."
    elif pontuacao >= 5:
        resultado = "25-50% de chance de ter lipedema"
        orientacao = "Há uma baixa chance de lipedema, mas, se os sintomas são persistentes, pode ser interessante investigar mais a fundo para esclarecer qualquer dúvida."
    else:
        resultado = "0-25% de chance de ter lipedema"
        orientacao = "A possibilidade de lipedema é muito baixa. Entretanto, sintomas persistentes ou incômodos podem exigir uma análise mais detalhada para trazer maior clareza."

    resultado_final = f"Sua pontuação: {pontuacao}\nResultado: {resultado}\n\n{orientacao}"
    
    agendamento = "\n\nCONSIDERAÇÕES FINAIS: Entender mais sobre o que você sente e como isso afeta seu dia a dia é essencial para viver com qualidade. Pensando nisso, oferecemos uma consulta inicial gratuita de 30 minutos com a Nutricionista Especialista em lipedema Silvia Martins. Esse momento é dedicado a ouvir você, compreender suas dores e traçar, de forma personalizada, as melhores abordagens para o seu bem-estar. Não se trata apenas de um diagnóstico, mas de um cuidado focado em você."

    # Concatenar agendamento ao resultado final
    resultado_final += agendamento
    
    # Inserir dados no banco de dados
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO dados_lipedema (nome_completo, email, idade, peso, profissao, whatsapp, pontuacao, resultado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        ''', (nome, email, idade, peso, profissao, whatsapp, pontuacao, resultado))
        conn.commit()
        cursor.close()
    except Exception as e:
        conn.close()
        return f"Erro ao salvar no banco de dados: {e}"

    # Fechar a conexão
    conn.close()

    return resultado_final

    # Perguntas e respostas com pontuações
questions = [
    ("PERGUNTA 01..: Você sente que tem algo errado nas suas pernas, mas não sabe o que?",
     ["Sim, pernas grandes, parecem troncos, gordura no tornozelo.", "Sim, pernas maiores comparadas ao corpo.", "Sim, pernas grandes e proporcionais.", "Não, minhas pernas estão bem."], [3, 2, 1, 0]),
    ("PERGUNTA 02..: Você percebe que a parte inferior do seu corpo (pernas, quadris) parece maior ou desproporcional ao tronco?",
     ["Sim, tamanho da calça é 3x maior que camisa.", "Sim, calça 1 a 2x maior que camisa.", "Não, tronco maior que a parte de baixo.", "Não, ambos proporcionais."], [2, 1, 0, 0]),
    ("PERGUNTA 03..: Você tem problema para perder peso, principalmente na parte de baixo do corpo?",
     ["Sim, não consigo perder peso, principalmente nas coxas/pernas/quadril/braços.", "Sim, perco peso no tronco, excluindo braços.", "Não, perco peso proporcionalmente.", "Não tenho problema de peso ou dificuldade para perder."], [2, 1, 0, 0]),
    ("PERGUNTA 04..: Você nota que suas pernas ou braços têm áreas onde a pele parece mais sensível ou dolorosa ao toque, comparada a outras partes do corpo?",
     ["Sim, áreas específicas são muito sensíveis e dolorosas ao toque.", "Sim, percebo sensibilidade em algumas áreas, mas sem dor intensa.", "Não, a sensibilidade é igual ao restante do corpo.", "Não, nunca percebi diferença na sensibilidade."], [2, 1, 0, 0]),
    ("PERGUNTA 05..: Você sente que há um acúmulo de gordura ou volume em suas pernas ou braços que se destaca mesmo com um peso corporal considerado normal?",
     ["Sim, há um acúmulo evidente, mesmo quando estou no peso ideal.", "Sim, há algum acúmulo visível, mas não muito acentuado.", "Não, o volume parece proporcional ao peso.", "Não, nunca notei diferenças relacionadas ao peso."], [2, 1, 0, 0]),
    ("PERGUNTA 06..: Você percebe que suas pernas ou braços parecem mais “pesados” ou desconfortáveis ao final do dia?",
     ["Sim, sinto peso e desconforto constantes ao final do dia.", "Sim, às vezes noto peso e desconforto, mas em dias mais longos ou quentes.", "Não, raramente percebo peso ou desconforto.", "Não, nunca sinto peso ou desconforto nessas áreas"], [2, 1, 0, 0]),
    ("PERGUNTA 07..: Suas pernas doem?",
     ["Sim, são muito sensíveis, dolorosas ou com sensação de queimação.", "Sim, dolorosas com qualquer toque.", "Às vezes, doem ao pressionar ou ficar muito tempo em pé.", "Não, não doem."], [3, 2, 1, 0]),
    ("PERGUNTA 08..: Você tem inchaço nas pernas?",
     ["Sim, incham quase o tempo todo, pioram no calor, e não melhora com elevação.", "Sim , frequentemente incham, mas melhora com elevação.", "Sim, às vezes incham no calor ou após longas viagens.", "Não, raramente sinto inchaço nas pernas."], [2, 1, 0, 0]),
    ("PERGUNTA 09..: Suas pernas ou braços formam hematomas facilmente?",
     ["Sim, formam hematomas muito facilmente, nem percebo como.", "Sim, formam hematomas com contato mínimo.", "Não, nunca formam hematomas."], [2, 1, 0]),
]

# Configuração do Gradio
inputs = [
    gr.Textbox(label="Nome Completo"),
    gr.Textbox(label="Email"),
    gr.Slider(minimum=0, maximum=120, step=1, label="Idade", elem_id="idade_slider"),
    gr.Number(label="Peso (kg)", precision=1),
    gr.Textbox(label="Profissão"),
    gr.Textbox(label="Whatsapp - Coloque o DDD e o Número Corretamente"),
]

for question, options, _ in questions:
    inputs.append(gr.Radio(label=question, choices=options))

output = gr.Textbox(label="Resultado Final")

interface = gr.Interface(
    fn=processar_formulario,
    inputs=inputs,
    outputs=output,
    title="Faça o Seu Teste e Descubra se Você Apresenta Sinais de LIPEDEMA",
    description="Esta ferramenta auxilia na identificação de sintomas de lipedema, mas não substitui diagnóstico profissional.",
    allow_flagging="never",
    theme="huggingface"
)

if __name__ == "__main__":
    interface.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 8080)))
