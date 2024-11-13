from IPython import get_ipython
from IPython.display import display
import os
import json
import gradio as gr
import psycopg2
import re

# Conectar ao banco de dados usando a URL fornecida pelo Heroku
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL, sslmode='require')

# Função para criar a tabela caso ainda não exista
def criar_tabela():
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

# Criar a tabela ao iniciar o sistema
criar_tabela()
        
# Perguntas e respostas com pontuações
questions = [
    ("Você sente que tem algo errado nas suas pernas, mas não sabe o que?",
     ["Sim, pernas grandes, parecem troncos, gordura no tornozelo.", "Sim, pernas maiores comparadas ao corpo.", "Sim, pernas grandes e proporcionais.", "Não, minhas pernas estão bem."], [3, 2, 1, 0]),
    ("A parte de baixo do corpo é maior e desproporcional ao tronco?",
     ["Sim, tamanho da calça é 3x maior que camisa.", "Sim, calça 1 a 2x maior que camisa.", "Não, tronco maior que a parte de baixo.", "Não, ambos proporcionais."], [2, 1, 0, 0]),
    ("Você tem problema para perder peso, principalmente na parte de baixo do corpo?",
     ["Sim, não consigo perder peso, principalmente nas coxas/pernas/quadril/braços.", "Sim, perco peso no tronco, excluindo braços.", "Não, perco peso proporcionalmente.", "Não tenho problema de peso ou dificuldade para perder."], [2, 1, 0, 0]),
    ("Durante a puberdade, você ganhou peso principalmente nas coxas/pernas/quadris/nádegas/braços?",
     ["Sim, ganhei muito peso, principalmente nas coxas/pernas/quadris/braços.", "Sim, ganhei algum peso nas coxas/pernas/quadris.", "Não, ganhei pouco peso, distribuído no corpo inteiro.", "Não, ganhei pouco ou nenhum peso."], [2, 1, 0, 0]),
    ("Durante ou logo após a gravidez/amamentação, você ganhou peso ou teve mudança nas coxas/pernas/quadris/nádegas/braços?",
     ["Sim, ganhei muito peso (mais de 23kg) nessas áreas.", "Sim, ganhei entre 16-23kg nessas áreas.", "Não, ganho de peso normal (11-15kg).", "Não, ganhei menos peso do que o esperado ou perdi peso."], [2, 1, 0, 0]),
    ("Durante a menopausa, você ganhou peso ou teve mudança nas coxas/pernas/quadris/nádegas/braços?",
     ["Sim, ganhei bastante peso, especialmente nessas áreas.", "Sim, ganhei peso e essas áreas cresceram um pouco.", "Não muito, ganhei pouco peso, distribuído no corpo.", "Não, não ganhei peso."], [2, 1, 0, 0]),
    ("Suas pernas doem?",
     ["Sim, são muito sensíveis, dolorosas ou com sensação de queimação.", "Sim, dolorosas com qualquer toque.", "Às vezes, doem ao pressionar ou ficar muito tempo em pé.", "Não, não doem."], [3, 2, 1, 0]),
    ("Você tem inchaço nas pernas?",
     ["Sim, incham quase o tempo todo, pioram no calor, e não melhora com elevação.", "Sim , frequentemente incham, mas melhora com elevação.", "Não, às vezes incham no calor ou após longas viagens.", "Não, raramente sinto inchaço nas pernas."], [2, 1, 0, 0]),
    ("Suas pernas ou braços formam hematomas facilmente?",
     ["Sim, formam hematomas muito facilmente, nem percebo como.", "Sim, formam hematomas com contato mínimo.", "Não formam hematomas facilmente."], [2, 1, 0]),
]

# Função para validar e-mail
def validar_email(email):
    # Expressão regular para e-mails válidos
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

# Função para validar telefone com DDD
def validar_telefone(telefone):
    # Expressão regular para telefone com 11 dígitos (somente números)
    telefone_regex = r'^\d{11}$'
    return re.match(telefone_regex, telefone) is not None

# Função para processar o formulário e gerar o resultado
def processar_formulario(nome, email, idade, peso, profissao, whatsapp, *respostas):
    # Verificação de campos vazios
    if not nome or not email or not idade or not peso or not profissao or not whatsapp:
        return "Por favor, preencha todas as informações pessoais."

    # Validação do e-mail
    if not validar_email(email):
        return "Por favor, insira um e-mail válido."

    # Validação do telefone (Whatsapp) com DDD
    if not validar_telefone(whatsapp):
        return "Por favor, insira um número de telefone válido com 11 dígitos (apenas números)."

    for resposta in respostas:
        if resposta is None:
            return "Por favor, responda todas as perguntas do questionário."

    # Cálculo da pontuação
    pontuacao = 0
    for i, resposta in enumerate(respostas):
        # Encontra o índice da opção selecionada
        option_index = questions[i][1].index(resposta)
        # Recupera a pontuação usando o option_index
        pontuacao += questions[i][2][option_index]

    # Definindo o resultado final com base na pontuação
    if pontuacao >= 13:
        resultado = "75-100% de chance de ter lipedema"
        orientacao = "Você tem uma alta chance de ter lipedema. É importante procurar um especialista para uma avaliação completa e tratamentos adequados."
    elif pontuacao >= 9:
        resultado = "50-75% de chance de ter lipedema"
        orientacao = "A chance de você ter lipedema é moderada. Recomenda-se buscar avaliação médica para confirmar o diagnóstico e discutir opções de tratamento."
    elif pontuacao >= 5:
        resultado = "25-50% de chance de ter lipedema"
        orientacao = "A chance de você ter lipedema é baixa, mas se você sentir algum sintoma, consulte um profissional para avaliação."
    else:
        resultado = "0-25% de chance de ter lipedema"
        orientacao = "A chance de você ter lipedema é muito baixa, mas se você tiver algum sintoma persistente, procure um especialista para mais informações."

    # Incentivo para agendamento de consulta
    agendamento = "\n\nPara um diagnóstico completo e personalizado, AGENDE UMA CONSULTA INICIAL GRATUITA DE 30 MINUTOS com a especialista certificada da Abrali Silvia Martins. Clique no Botão do Whatsapp para agendar."

    # Resultado final com orientações e incentivo para agendamento
    resultado_final = f"Sua pontuação: {pontuacao}\nResultado: {resultado}\n\n{orientacao}{agendamento}"

    # Salvando os dados no banco de dados PostgreSQL
    try:
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO dados_lipedema (nome, email, idade, peso, profissao, whatsapp, pontuacao, resultado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        ''', (nome, email, idade, peso, profissao, whatsapp, pontuacao, resultado))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return f"Erro ao salvar no banco de dados: {e}"

    # Retorna o resultado final
    return resultado_final

# Modifique os campos de idade e peso para aceitar apenas números
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

# Executando o Gradio com melhorias de layout
interface = gr.Interface(
    fn=processar_formulario,
    inputs=inputs,
    outputs=output,
    title="Faça o Seu Teste e Descubra se Você Apresenta Sinais de LIPEDEMA",
    description="Responda algumas perguntas rápidas e veja sua chance de ter lipedema. Esta ferramenta foi criada para auxiliá-la na identificação de sintomas, mas não substitui um diagnóstico profissional. Para uma avaliação completa e precisa, consulte um especialista.",
    allow_flagging="never",
    theme="huggingface"
)

# Gera o link compartilhável
interface.launch(share=True)
