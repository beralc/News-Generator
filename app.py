import os
from flask import Flask, render_template, request, redirect, url_for, flash
import openai
import markdown
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "KEY DE FLASK"

# CONFIGURACIÓN OPEN AI
openai.api_key = 'API OPEN AI'

# CONFIG DE BASE DE DATOS
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mylocaldb.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# MODELO DE BBDD
class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(50))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content_type = request.form.get('content_type')  

        # AQUÍ SE RECUPERAN LOS DATOS DEL FORMULARIO
        date = request.form.get('date')
        location = request.form.get('location')
        description = request.form.get('description')
        objective = request.form.get('objective')
        entities = request.form.get('entities')
        details = request.form.get('details')
        opinions = request.form.get('opinions')
        context = request.form.get('context')
        actions = request.form.get('actions')
        contact = request.form.get('contact')

        # INTRO DE PROMPT
        prompt_intro = ""

        # ACTUALIZA EL PROMPT
        if content_type == "news":
            prompt_intro = "escribe un artículo para una web usando la siguiente información:"
        elif content_type == "press_release":
            prompt_intro = "escribe un comunicado de prensa usando la siguiente información:"
        else:
            flash('Invalid content type', 'danger')
            return redirect(url_for('index'))
        
        prompt_text = f"{prompt_intro} {location} {description} {objective} {entities} {details} {opinions} {context} {actions} {contact}.Recuerda utilizar párrafos que no sean demasiado cortos y separarlos con un salto de línea. Siempre después del texto, haz una sección llamada 'Redes sociales' y escribe 3 propuestas de publicaciones de Instagram con emoticones y hashtags. Asegúrate que el texto no suene cursi."

        # DEFINICIÓN DE ROL
        messages = [
                {"role": "system", "content": "Eres un experto de marketing y comunicación que se especializa en escribir contenido basado en las aportaciones del usuario. Genera contenido basado en la siguiente información. Recuerda hacerlo SEO friendly: y recuerda que todos los artículos serán en castellano"},
            {"role": "user", "content": prompt_text}
        ]
        
        response = openai.ChatCompletion.create(
            model="gpt-4", 
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        content_generated = response.choices[0].message['content'].strip()
        
        
        content_html = markdown.markdown(content_generated)

        new_content = Content(content_type=content_type, content=content_html)
        
        db.session.add(new_content)
        db.session.commit()

        flash('Content generated and saved successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('form.html')

@app.route('/content', methods=['GET', 'POST'])
def all_content():
    content_type = request.args.get('type')
    search_word = request.args.get('query')
    
    query = Content.query
    
    if search_word:
        query = query.filter(Content.content.contains(search_word))
    
    if content_type:
        if content_type == "news":
            query = query.filter_by(content_type="news")
        elif content_type == "press_release":
            query = query.filter_by(content_type="press_release")

    contents = query.order_by(Content.timestamp.desc()).all()
    return render_template('all_content.html', contents=contents)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)