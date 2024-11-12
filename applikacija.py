# Import potrebnih biblioteka i modula
from io import BytesIO
from flask import Flask, flash, render_template, request, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,timezone
from sqlalchemy import func
import base64
import os
from flask_login import UserMixin,login_user, LoginManager, login_required,logout_user,current_user
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

# Inicijalizacija aplikacije i konfiguracija baze podataka
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///baza_nova.db'  # Putanja do SQLite baze podataka
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Onemogućavanje upozorenja o promjenama
app.secret_key = 'nikola'  # Tajni ključ za sesije
db = SQLAlchemy(app)  # Inicijalizacija SQLAlchemy
bcrypt=Bcrypt(app)
app.app_context().push()

# Definiranje korisničkog modela, uključujući polja za ime, prezime, korisničko ime i lozinku
class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    ime = db.Column(db.String(50), nullable=False)
    prezime = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    
    # Relacije sa ostalim tabelama
    kategorije = db.relationship('Kategorija', backref='user', lazy=True)
    potrosnja = db.relationship('Potrosnja', backref='user', lazy=True)

# Definranje modela Kategorija za praćenje kategorija troškova
class Kategorija(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    naziv = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Definiranje modela Potrosnja za praćenje pojedinačnih troškova
class Potrosnja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kategorija = db.Column(db.String(50))
    trosak = db.Column(db.String(50))
    naziv_slike = db.Column(db.String(50))
    slika = db.Column(db.LargeBinary)
    datum = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Konfiguracija za autentifikaciju i sesiju korisnika
login_manager= LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'

# Funkcija za učitavanje korisnika prema njihovom ID-u, potrebna za Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

# Kreiranje forme za registraciju korisnika sa validacijom unosa
class RegisterForm(FlaskForm):
    ime = StringField(validators=[InputRequired(), Length(min=2, max=50)], render_kw={'placeholder': 'Ime'})
    prezime = StringField(validators=[InputRequired(), Length(min=2, max=50)], render_kw={'placeholder': 'Prezime'})
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={'placeholder': 'Username'})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={'placeholder': 'Password'})
    submit = SubmitField('Registriraj se')
    def validate_username(self,username):
        postojeci_user_username= User.query.filter_by(username=username.data).first()
        if postojeci_user_username:
            raise ValidationError('Ovo korisničko ime vec postoji. Molim, odaberite drugo.')

# Kreiranje forme za prijavu korisnika
class LoginForm(FlaskForm):
    username =StringField(validators=[InputRequired(),Length(min=4,max=20)],render_kw={'placeholder': 'unesite email'})
    password =PasswordField(validators=[InputRequired(),Length(min=4,max=20)],render_kw={'placeholder': 'unesite password'})
    submit= SubmitField('Prijavi se')


# Ruta za login formu sa validacijom lozinke
@app.route('/',methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user= User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password,form.password.data):
                login_user(user)
                flash('Dobro došli..')
                return redirect(url_for('pocetna'))
            else:
                flash("Pogrešna lozinka - Pokušajte ponovno!")
        else:
            flash("Korisnik ne postoji! Pokušajte ponovno...")
    
    return render_template('login.html',form=form)

# Ruta za registraciju novih korisnika 
@app.route('/signup',methods=['GET','POST'])
def signup():
    form=RegisterForm()
    if form.validate_on_submit():
        hashed_password= bcrypt.generate_password_hash(form.password.data)
        noviKorisnik = User(
            ime=form.ime.data,
            prezime=form.prezime.data,
            username=form.username.data,
            password=hashed_password
        )
        db.session.add(noviKorisnik)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('signup.html',form=form)

# Ruta za odjavu korisnika
@app.route('/logout',methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    flash("Upravo ste se odjavili!  Navrati ponovno...")
    return redirect(url_for('login'))



# Glavna stranica aplikacije
@login_required
@app.route('/pocetna')
def pocetna():

    datum = datetime.now(timezone.utc).date()
    # Izdvajanje podataka iz baze za trenutni mjesec
    mjesec = datum.strftime('%m')
    trenutni_mj = Potrosnja.query.filter(func.strftime('%m', Potrosnja.datum) == mjesec,
    Potrosnja.user_id == current_user.id).all()
    
    if not trenutni_mj:
        najveci = 0
        trosak = 0
    else:
        potroseno = [float(red.trosak) for red in trenutni_mj]
        najveci = max(potroseno)
        trosak = sum(potroseno)

    return render_template('index.html', trosak=trosak, datum=datum, najveci=najveci)

    
# Preuzimanje slike prema ID-u
@login_required
@app.route('/download/<int:upload_id>')
def download(upload_id):
    potrosnja = Potrosnja.query.get_or_404(upload_id)  # Dohvati potrošnju prema ID-u
    return send_file(BytesIO(potrosnja.slika), download_name=potrosnja.naziv_slike, as_attachment=True)

# Prikaz slike
@login_required
@app.route('/slika/<int:image_id>')
def slika(image_id):
    image = Potrosnja.query.get_or_404(image_id)  # Dohvati sliku prema ID-u
    return send_file(BytesIO(image.slika), mimetype='image/jpeg')

# Odabir računa za detalje
@login_required
@app.route('/odabir_racuna/<int:upload_id>')
def odabir_racuna(upload_id):
    potrosnja = Potrosnja.query.get_or_404(upload_id)  # Dohvati potrošnju prema ID-u
    image_url = url_for('download', upload_id=upload_id)  # URL za preuzimanje slike
    return render_template('pregled_racuna.html', potrosnja=potrosnja, image_url=image_url)

# Prikaz svih potrošnja za trenutni mjesec
@login_required
@app.route('/trenutna_potrosnja')
def trenutna_potrosnja():
    datum = datetime.now(timezone.utc)
    godina = datum.strftime('%Y')
    mjesec = datum.strftime('%m')
    
    # Filter records where both the year and month match
    potrosnja = Potrosnja.query.filter(
        func.strftime('%Y', Potrosnja.datum) == godina,
        func.strftime('%m', Potrosnja.datum) == mjesec,
        Potrosnja.user_id == current_user.id).all()
    
    
    if not potrosnja:
        flash('Trenutno nema podataka u bazi...')
        return render_template('trenutna_potrosnja.html')

    return render_template('trenutna_potrosnja.html', potrosnja=potrosnja, nm=mjesec, yr=godina)

# Statistika potrošnje
@login_required
@app.route('/statistika_info')
def statistika():
    # Dohvatanje trenutnog mjeseca i godine
    trenutni_mjesec = datetime.now(timezone.utc).strftime('%m')  # Trenutni mjesec u formatu MM 
    trenutna_godina = datetime.now(timezone.utc).strftime('%Y')  # Trenutna godina u formatu YYYY

    # Dohvatanje svih troškova korisnika za trenutni mjesec grupisanih po kategorijama
    troskovi_po_kategorijama = (
        Potrosnja.query
        .filter(
            Potrosnja.user_id == current_user.id,  # Filter prema korisniku
            func.strftime('%Y', Potrosnja.datum) == trenutna_godina,  # Filter prema godini
            func.strftime('%m', Potrosnja.datum) == trenutni_mjesec  # Filter prema mjesecu
        )
        .group_by(Potrosnja.kategorija)  # Grupiranje po kategorijama
        .with_entities(Potrosnja.kategorija, func.sum(Potrosnja.trosak).label('ukupno_trosak'))  # Suma troškova po kategoriji
        .all()  # Izvršavanje upita
    )

    # Ako nema troškova, postavite praznu listu
    if not troskovi_po_kategorijama:
        troskovi_po_kategorijama = []

    # Izdvajanje naziva kategorija i ukupnih troškova
    kategorije = [trosak.kategorija for trosak in troskovi_po_kategorijama]
    ukupno_trosak = [trosak.ukupno_trosak for trosak in troskovi_po_kategorijama]

    
    return render_template('potrosnja_trenutna.html', kategorije=kategorije, trosak=ukupno_trosak)

# Ruta za dodavanje troškova/ potrebno je prije dodati kategoriju
@login_required
@app.route('/dodaj_trosak', methods=['GET', 'POST'])
def dodaj_trosak():

     # Korisnik je već automatski prepoznat putem current_user
    user = current_user

    # Dohvacanje svih kategorija vezanih za korisnika
    kategorije = Kategorija.query.filter_by(user_id=user.id).all()
    kategorija_names = [kategorija.naziv for kategorija in kategorije] if kategorije else []

    if request.method == 'POST':
        try:
            file = request.files.get('file')  
            trosak = request.form.get('trosak')
            kategorija = request.form.get('kategorija')
            datum = datetime.utcnow().date()

            # Provjera da li unesena/odabrana sva polja sa forma osim filea
            if trosak and kategorija:
                if file and file.filename != '':  # ako je file prilozen i njegovo ime
                    image_data = file.read()
                    image_name = file.filename

                else:  # Koristi default sliku ako nije file prilozen
                    default_image_path = os.path.join('static', 'logo.png')
                    with open(default_image_path, 'rb') as default_image:
                        image_data = default_image.read()
                        image_name = 'logo.png'

                # Kreiranje Potrosnja instance
                potrosnja = Potrosnja(
                    user_id=user.id,  # povezivanje sa korisnikom
                    kategorija=kategorija,
                    trosak=trosak,
                    naziv_slike=image_name,
                    slika=image_data,
                    datum=datum
                )
                db.session.add(potrosnja)  # Dodavanje novih podataka
                db.session.commit()  # Spremi potvrdi sesiju
                flash('Podaci uspješno dodani...')
                return redirect(url_for('dodaj_trosak'))
            else:
                flash('Molim, unesite sve podatke.')
                return redirect(url_for('dodaj_trosak'))

        except Exception as e:
            db.session.rollback()  # Vrati promjene ako se pojavi error 
            flash(f'Error: {str(e)}')  # Pokazi error
            return redirect(url_for('dodaj_trosak'))

    return render_template('dodaj_trosak.html', user=user, kategorije=kategorija_names)


@login_required
@app.route('/potrosnja_zadnjih_pet')
def potrosnja_zadnjih_pet():
    # Dohvatanje najvećih 5 troškova korisnika
    najveci_troskovi = (
        Potrosnja.query
        .filter_by(user_id=current_user.id)  # Filtrira prema korisniku
        .order_by(Potrosnja.trosak.desc())  # Sortira od najvećeg troška prema najmanjem
        .limit(5)  # Ograničava rezultat na 5 najvećih
        .all()
    )

    # Priprema podataka za predložak
    troskovi_iznosi = [trosak.trosak for trosak in najveci_troskovi]
    troskovi_kategorije = [trosak.kategorija for trosak in najveci_troskovi]
    
    # Prosljeđivanje podataka u predložak
    return render_template('potrosnja_zadnjih_pet.html', troskovi_iznosi=troskovi_iznosi, troskovi_kategorije=troskovi_kategorije)


@app.route('/ukupna_potrosnja_po_kategorijama')
@login_required
def ukupna_potrosnja_po_kategorijama():
    # Dohvatanje svih troškova korisnika grupiraanih po kategorijama
    troskovi_po_kategorijama = (
        Potrosnja.query
        .filter(Potrosnja.user_id == current_user.id)  # Filter prema korisniku
        .group_by(Potrosnja.kategorija)  # Grupiranje po kategorijama
        .with_entities(Potrosnja.kategorija, func.sum(Potrosnja.trosak).label('ukupno_trosak'))  # Suma/zbroj troškova po kategoriji
        .all()  # Izvršavanje upita
    )

    # Ako nema troškova, postavite praznu listu
    if not troskovi_po_kategorijama:
        troskovi_po_kategorijama = []

    # Izdvajanje naziva kategorija i ukupnih troškova
    kategorije = [trosak.kategorija for trosak in troskovi_po_kategorijama]
    ukupno_trosak = [trosak.ukupno_trosak for trosak in troskovi_po_kategorijama]

    # Prosljeđivanje podataka u predložak
    return render_template('ukupna_potrosnja_po_kategorijama.html', kategorije=kategorije, ukupno_trosak=ukupno_trosak)


# Definiranje rute za mjesecnu potrosnju
@login_required
@app.route('/potrosnja_po_mjesecima')
def potrosnja_po_mjesecima():
    # Grupiranje po mjesecu i godini, zbrajanje troskova za svaki mjesec
    monthly_spending = (
        Potrosnja.query.with_entities(
            func.strftime('%Y-%m', Potrosnja.datum).label('month'),  
            func.sum(Potrosnja.trosak).label('total_spent'),
            
        )
        .filter(Potrosnja.user_id == current_user.id)  # Filtriraj po trenutnom korisniku
        .group_by('month')
        .order_by('month')
        .all())

    if not monthly_spending:
        flash('Trenutno nema zapisa u bazi...')
        return render_template('potrosnja_po_mjesecu.html')
  
    return render_template('potrosnja_po_mjesecu.html', monthly_spending=monthly_spending)


@login_required
@app.route('/statistika_podaci')
def statistika_podaci():
    posljednji_troskovi = (
        Potrosnja.query
        .filter(Potrosnja.user_id == current_user.id)  # Filtriranje po korisniku        
        .order_by(Potrosnja.datum.desc())  # Sortiranje po datumu opadajuće
        .limit(5)  # Ograničenje na posljednja 5 troška
        .all()
    )

    # Ako nema podataka
    if not posljednji_troskovi:
        labels=0
        values=0
        flash('Nemate poslednjih troškova za prikazivanje.')
        return render_template('statistika.html',labels=labels, values=values)

    # Priprema podataka za grafikon
    labels = [trosak.kategorija for trosak in posljednji_troskovi]
    values = [float(trosak.trosak) for trosak in posljednji_troskovi]

    # Prosljeđivanje podataka u predložak
    return render_template('statistika.html',posljednji_troskovi=posljednji_troskovi, labels=labels, values=values ) 


@login_required
@app.route('/prikaz_troskova')
def prikaz_troskova():
    month = request.args.get('month')  # Dohvati odabrani mjesec iz URL parametara
    
    potrosnja = Potrosnja.query.filter(func.strftime('%Y-%m', Potrosnja.datum) == month,
                                       Potrosnja.user_id == current_user.id).all()
    
    return render_template('prikaz_troskova.html', potrosnja=potrosnja, selected_month=month)


@app.route('/dodaj_kategoriju', methods=['GET', 'POST'])
@login_required  # Ova ruta je dostupna samo prijavljenim korisnicima
def dodaj_kategoriju():
    if request.method == 'POST':
        naziv = request.form.get('naziv')  # Dohvati naziv kategorije iz forme

        if naziv:
            # Kreiraj novu kategoriju povezanu sa trenutnim korisnikom
            nova_kategorija = Kategorija(naziv=naziv, user_id=current_user.id)
            db.session.add(nova_kategorija)
            db.session.commit()
            flash('Kategorija dodana.')
            return redirect(url_for('prikazi_kategorije'))  # Nakon što je kategorija dodata, prikazujemo listu kategorija

        else:
            return "Molimo unesite naziv kategorije.", 400  # Ako naziv nije unesen, vratimo grešku

    return render_template('dodaj_kategoriju.html')  # Vraćamo formu za unos nove kategorije

@app.route('/kategorije')
@login_required  
def prikazi_kategorije():
    # Dohvati sve kategorije vezane za trenutnog korisnika
    kategorije = Kategorija.query.filter_by(user_id=current_user.id).all()
    return render_template('kategorije.html', kategorije=kategorije)


@app.route('/izbrisi_iz_kategorije/<int:kategorija_id>', methods=['GET', 'POST'])
@login_required  
def izbrisi_iz_kategorije(kategorija_id):
    # Dohvati sve kategorije vezane za trenutnog korisnika
    kategorija = Kategorija.query.filter_by(id=kategorija_id, user_id=current_user.id).first()

    if kategorija:
        db.session.delete(kategorija)
        db.session.commit()
        flash('Unos je obrisan')
    else:
        flash('Unos nije pronađen ili nemate dozvolu za brisanje.')
    
    kategorije = Kategorija.query.filter_by(user_id=current_user.id).all()
    return render_template('kategorije.html', kategorije=kategorije)


# Pokretanje aplikacije
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Kreiraj tablicu u bazi ako ne postoji
    app.run()

# THE END