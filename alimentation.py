import requests
from lxml import html
import urllib.parse

fs = open("alimentation.sql", "w")

noms = ["prix_auteur", "prix_oeuvre"]

noms_prix = {}

noms_prix["prix_auteur"] = ['Goncourt', 'Renaudot', 'Femina', 'Goncourt des lycéens', 'Nobel de Littérature']
noms_prix["prix_oeuvre"] = ['Livre Inter', 'Des Libraires', 'Roman Fnac', 'Médicis']

fs.write("ALTER TABLE oeuvre ALTER COLUMN nom_oeuvre TYPE VARCHAR(100);\n\nALTER TABLE attribution_prix_auteur DROP CONSTRAINT attribution_prix_auteur_pkey;\nALTER TABLE attribution_prix_auteur ADD PRIMARY KEY (id_prix, id_auteur);\n\nALTER TABLE attribution_prix_oeuvre DROP CONSTRAINT attribution_prix_oeuvre_pkey;\nALTER TABLE attribution_prix_oeuvre ADD PRIMARY KEY (id_prix, id_oeuvre);\n\n")

#alimentation de prix_auteur et prix_oeuvre
for nom in noms:
	fs.write("INSERT INTO {}(nom_prix) VALUES\n".format(nom))

	for i in range(len(noms_prix[nom])):
		if i < len(noms_prix[nom])-1:
			c = ',\n'
		else:
			c = ';\n\n'
		fs.write("\t('{}'){}".format(noms_prix[nom][i], c))

#alimentation auteur
urls_auteur = ['https://fr.wikipedia.org/wiki/Prix_Goncourt', 'https://fr.wikipedia.org/wiki/Prix_Renaudot', 'https://fr.wikipedia.org/wiki/Prix_Femina', 'https://fr.wikipedia.org/wiki/Prix_Goncourt_des_lyc%C3%A9ens', 'https://fr.wikipedia.org/wiki/Prix_Nobel_de_litt%C3%A9rature']
urls_oeuvre = ['https://fr.wikipedia.org/wiki/Prix_du_Livre_Inter', 'https://fr.wikipedia.org/wiki/Prix_des_libraires', 'https://fr.wikipedia.org/wiki/Prix_du_roman_Fnac', 'https://fr.wikipedia.org/wiki/Prix_M%C3%A9dicis']

liste_auteur = []
liste_oeuvre = []
ecriture = []
attribution_prix_auteur = []
attribution_prix_oeuvre = []

print("Récolte des auteurs et oeuvres...")
for url in urls_auteur:
	print(urllib.parse.unquote(url))
	page = requests.get(url)

	tree = html.fromstring(page.content)
	
	if url == 'https://fr.wikipedia.org/wiki/Prix_Nobel_de_litt%C3%A9rature':
		lignes = tree.xpath("//table/tbody/tr/td/ul/li")
		for ligne in lignes:
			liens = ligne.xpath("./a")
			if len(liens) > 1:
				t = liens[1].text
				if not t.isdigit():
					if t not in liste_auteur:
						liste_auteur += [t]
						t = (urls_auteur.index(url), liens[0].text, liste_auteur.index(t))
						if t not in attribution_prix_auteur:
							attribution_prix_auteur += [t]
	elif url == 'https://fr.wikipedia.org/wiki/Prix_Interalli%C3%A9':#cas particulier
		lignes = tree.xpath("//table/tbody/tr")
		for ligne in lignes:
			a = ligne.xpath("./td/a")
			auteurs_tmp = []
			if a:
				auteurs_tmp += [a[1].text]
				if a[1].text not in liste_auteur:
					liste_auteur += [a[1].text]
					t = (urls_auteur.index(url), a[0].text, liste_auteur.index(a[1].text))
					if t not in attribution_prix_auteur:
						attribution_prix_auteur += [t]
			for i in ligne.xpath("./td/i/a"):
				if i.text not in liste_oeuvre:
					liste_oeuvre += [i.text]
					for auteur_i in auteurs_tmp:
						t = (liste_auteur.index(auteur_i), liste_oeuvre.index(i.text))
						if t not in ecriture:
							ecriture += [t]
	else:
		lignes = tree.xpath("//center/table/tbody/tr")
		for ligne in lignes:
			a = ligne.xpath("./td")
			auteurs_tmp = []
			if len(a) > 3:
				for i in a[2].xpath("./a"):
					auteurs_tmp += [i.text]
					if i.text not in liste_auteur:
						liste_auteur += [i.text]
						t = (urls_auteur.index(url), a[0].xpath("./a")[0].text, liste_auteur.index(i.text))
						if t not in attribution_prix_auteur:
							attribution_prix_auteur += [t]
			for i in ligne.xpath("./td/i/a"):
				if i.text not in liste_oeuvre:
					liste_oeuvre += [i.text]
					for auteur_i in auteurs_tmp:
						t = (liste_auteur.index(auteur_i), liste_oeuvre.index(i.text))
						if t not in ecriture:
							ecriture += [t]

for url in urls_oeuvre:
	print(urllib.parse.unquote(url))
	page = requests.get(url)
	
	tree = html.fromstring(page.content)

	lignes = tree.xpath("//table/tbody/tr")
	for ligne in lignes:
		cellules = ligne.xpath("./td")
		auteurs_tmp = []
		if len(cellules) > 2:
			for i in cellules[2].xpath("./a"):
				auteurs_tmp += [i.text]
				if i.text not in liste_auteur:
					liste_auteur += [i.text]
			for i in cellules[3].xpath("./i/a"):
				if i.text not in liste_oeuvre:
					liste_oeuvre += [i.text]
					t = (urls_oeuvre.index(url), cellules[0].xpath('./a')[0].text, liste_oeuvre.index(i.text))
					if t not in attribution_prix_oeuvre:
						attribution_prix_oeuvre += [t]
					for auteur_i in auteurs_tmp:
						t = (liste_auteur.index(auteur_i), liste_oeuvre.index(i.text))
						if t not in ecriture:
							ecriture += [t]
	
print("Traitement et écriture...")

def forma(t):
	t = t.split(' ')
	if len(t) > 1:
		a = "'{}'".format(" ".join(t[1:]).replace("'", "''"))
	else:
		a = 'NULL'
	return "\t({}, '{}')".format(a, t[0].replace("'", "''"))

fs.write("INSERT INTO auteur(nom_auteur, prenom_auteur) VALUES\n")
print(*map(forma, liste_auteur), sep=',\n', end=';\n\n', file=fs)

def forma(s):
	return "\t('{}')".format(s.replace("'", "''"))

fs.write("INSERT INTO oeuvre(nom_oeuvre) VALUES\n")
print(*map(forma, liste_oeuvre), sep=',\n', end=';\n\n', file=fs)

def forma(t):
	return (int(t[0])+1, int(t[1])+1)

fs.write("INSERT INTO ecriture(id_auteur, id_oeuvre) VALUES\n\t")
print(*map(forma, ecriture), sep=',\n\t', end=';\n\n', file=fs)

def forma(t):
	return (int(t[0])+1, t[1], int(t[2])+1)

fs.write("INSERT INTO attribution_prix_auteur(id_prix, annee, id_auteur) VALUES\n\t")
print(*map(forma, attribution_prix_auteur), sep=',\n\t', end=';\n\n', file=fs)

fs.write("INSERT INTO attribution_prix_oeuvre(id_prix, annee, id_oeuvre) VALUES\n\t")
print(*map(forma, attribution_prix_oeuvre), sep=',\n\t', end=';\n\n', file=fs)

fs.close()

print("Fini !")
