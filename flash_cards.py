import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash

app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'db', 'cards.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('CARDS_SETTINGS', silent=True)


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    db = get_db()
    with app.open_resource('data/schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


# -----------------------------------------------------------

# Uncomment and use this to initialize database, then comment it
#   You can rerun it to pave the database and start over
#@app.route('/initdb')
#def initdb():
#    init_db()
#    return 'Base de donnée initialisée.'


@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('cpp'))
    else:
        return redirect(url_for('login'))


@app.route('/cartes')
def cards():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    query = '''
        SELECT id, type, front, back, known
        FROM cards
        ORDER BY id DESC
    '''
    cur = db.execute(query)
    cards = cur.fetchall()
    return render_template('cards.html', cards=cards, filter_name="all")


@app.route('/filtrer/<filter_name>')
def filter_cards(filter_name):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    filters = {
        "all":      "where 1 = 1",
        "cpp":  "where type = 1",
        "web":     "where type = 2",
        "alglin":     "where type = 3",
        "mathdi":     "where type = 4",
        "eco":     "where type = 5",
        "systeme":     "where type = 6",
        "known":    "where known = 1",
        "unknown":  "where known = 0",
    }
    
#CAT HERE

    query = filters.get(filter_name)

    if not query:
        return redirect(url_for('cards'))

    db = get_db()
    fullquery = "SELECT id, type, front, back, known FROM cards " + query + " ORDER BY id DESC"
    cur = db.execute(fullquery)
    cards = cur.fetchall()
    return render_template('cards.html', cards=cards, filter_name=filter_name)


@app.route('/ajouter', methods=['POST'])
def add_card():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    db.execute('INSERT INTO cards (type, front, back) VALUES (?, ?, ?)',
               [request.form['type'],
                request.form['front'],
                request.form['back']
                ])
    db.commit()
    flash('Nouvelle carte bien ajoutée.')
    return redirect(url_for('cards'))


@app.route('/modifier/<card_id>')
def edit(card_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    query = '''
        SELECT id, type, front, back, known
        FROM cards
        WHERE id = ?
    '''
    cur = db.execute(query, [card_id])
    card = cur.fetchone()
    return render_template('edit.html', card=card)


@app.route('/modifier_carte', methods=['POST'])
def edit_card():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    selected = request.form.getlist('known')
    known = bool(selected)
    db = get_db()
    command = '''
        UPDATE cards
        SET
          type = ?,
          front = ?,
          back = ?,
          known = ?
        WHERE id = ?
    '''
    db.execute(command,
               [request.form['type'],
                request.form['front'],
                request.form['back'],
                known,
                request.form['card_id']
                ])
    db.commit()
    flash('Carte sauvegardée.')
    return redirect(url_for('cards'))


@app.route('/supprimer/<card_id>')
def delete(card_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    db.execute('DELETE FROM cards WHERE id = ?', [card_id])
    db.commit()
    flash('Carte supprimé.')
    return redirect(url_for('cards'))


@app.route('/cpp')
@app.route('/cpp/<card_id>')
def cpp(card_id=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return memorize("cpp", card_id)


@app.route('/web')
@app.route('/web/<card_id>')
def web(card_id=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return memorize("web", card_id)

@app.route('/alglin')
@app.route('/alglin/<card_id>')
def alglin(card_id=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return memorize("alglin", card_id)

@app.route('/mathdi')
@app.route('/mathdi/<card_id>')
def mathdi(card_id=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return memorize("mathdi", card_id)

@app.route('/eco')
@app.route('/eco/<card_id>')
def eco(card_id=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return memorize("eco", card_id)

@app.route('/systeme')
@app.route('/systeme/<card_id>')
def systeme(card_id=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return memorize("systeme", card_id)

#CAT HERE

def memorize(card_type, card_id):
    if card_type == "cpp":
        type = 1
    elif card_type == "web":
        type = 2
    elif card_type == "alglin":
        type = 3
    elif card_type == "mathdi":
        type = 4
    elif card_type == "eco":
        type = 5
    elif card_type == "systeme":
        type = 6 #Add cat here
    else:
        return redirect(url_for('cards'))

    if card_id:
        card = get_card_by_id(card_id)
    else:
        card = get_card(type)
    if not card:
        flash("Vous avez appris toutes les cartes " + card_type + ".")
        return redirect(url_for('cards'))
    short_answer = (len(card['back']) < 75)
    return render_template('memorize.html',
                           card=card,
                           card_type=card_type,
                           short_answer=short_answer)


def get_card(type):
    db = get_db()

    query = '''
      SELECT
        id, type, front, back, known
      FROM cards
      WHERE
        type = ?
        and known = 0
      ORDER BY RANDOM()
      LIMIT 1
    '''

    cur = db.execute(query, [type])
    return cur.fetchone()


def get_card_by_id(card_id):
    db = get_db()

    query = '''
      SELECT
        id, type, front, back, known
      FROM cards
      WHERE
        id = ?
      LIMIT 1
    '''

    cur = db.execute(query, [card_id])
    return cur.fetchone()


@app.route('/marquer_appris/<card_id>/<card_type>')
def mark_known(card_id, card_type):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    db.execute('UPDATE cards SET known = 1 WHERE id = ?', [card_id])
    db.commit()
    flash('Carte marquée comme apprise!')
    return redirect(url_for(card_type))


@app.route('/connexion', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Identifiant ou mot de passe incorrect!'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Identifiant ou mot de passe incorrect!'
        else:
            session['logged_in'] = True
            session.permanent = True  # stay logged in
            return redirect(url_for('cards'))
    return render_template('login.html', error=error)


@app.route('/dexonnexion')
def logout():
    session.pop('logged_in', None)
    flash("Vous vous êtes déconnecté!")
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
