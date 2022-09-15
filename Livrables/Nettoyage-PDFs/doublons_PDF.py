import glob
import os
import argparse

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("directory", help="répertoire à traiter")
arg_parser.add_argument("output", help="dossier à créer pour la sortie des pdfs nettoyés")


class Range(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __eq__(self, other):
        return self.start <= other <= self.end

    def __contains__(self, item):
        return self.__eq__(item)

    def __iter__(self):
        yield self


arg_parser.add_argument("similarity", help="degré de similarité souhaité pour la comparaison des images", type=float,
                        choices=Range(0.0, 1.0))
args = arg_parser.parse_args()

# pour découper les pdf en images
from pdf2image import convert_from_path

# Import pour obtenir un hasher qui repère les doublons dans les images
from imagededup.methods import CNN

# Pour recréer le PDF
import img2pdf


def crop(files, type, path):
    """
    Fonction qui permet de découper une partie d'une image
    :param files: liste d'images qui constituent les pages du PDF
    :param type: zone de l'image à découper
    :param path: chemin pour le dossier de travail
    """
    n = 1
    path_dir = os.path.join(path, type)
    for im in files:
        if type == 'zone1':
            os.makedirs(path_dir, exist_ok=True)
            # Size of the image in pixels (size of original image)
            # (This is not mandatory)
            width, height = im.size

            # Setting the points for cropped image
            left = width / 2.4
            top = height / 2.2
            right = width / 1.8
            bottom = height / 1.6

            # Cropped image of above dimension
            # (It will not change original image)
            im_crop = im.crop((left, top, right, bottom))
            im_crop.save(os.path.join(path_dir, f"{n}.png"))
            n = n + 1

        if type == 'zone2':
            os.makedirs(path_dir, exist_ok=True)
            width, height = im.size

            left = width / 2.2  # 2.8
            top = height / 2.8
            right = width / 1.9  # 1.8
            bottom = height / 2.2

            im_crop = im.crop((left, top, right, bottom))
            im_crop.save(os.path.join(path_dir, f"{n}.png"))
            n = n + 1

        if type == 'zone3':
            os.makedirs(path_dir, exist_ok=True)
            width, height = im.size

            left = width * 0.1
            top = height * 0.05
            right = width * 0.3
            bottom = height * 0.4

            im_crop = im.crop((left, top, right, bottom))
            im_crop.save(os.path.join(path_dir, f"{n}.png"))
            n = n + 1


def find_duplicates(dir):
    """
    Fonction pour calculer le degré de ressemblance entre les images
    :param dir: répertoire des images du pdf à traiter
    """
    # on configure l'outil de comparaison
    cnn = CNN()
    # on récupère les images dans le dossier souhaité et on les encode
    encodings_zone1 = cnn.encode_images(image_dir=f"{dir}/zone1")
    # on compare l'encodage des images entre elles
    # min_similarity_threshold=0.96 : seuil à partir duquel on évalue qu'il y a un doublon pour les imprimés
    duplicates_zone1 = cnn.find_duplicates(encoding_map=encodings_zone1, min_similarity_threshold=args.similarity)

    # # on crée un dictionnaire vide pour stocker le résultat
    resultats_zone1 = {}

    for key, values in duplicates_zone1.items():
        # on crée une liste vide pour y stocker les numéros d'image en int
        liste_doublons = []
        # s'il y a des valeurs pour la clé, on conserve l'item, en ajoutant la clé et la liste d'int dans le dictionnaire
        if values:
            # on ajoute les numéros de chaque image doublons
            for value in values:
                liste_doublons.append(int(value.split(".")[0]))
            resultats_zone1[key] = liste_doublons
            # on ajoute aussi le numero de la clé en int pour pouvoir classer par ordre croissant les images
            resultats_zone1[key].append(int(key.split(".")[0]))
            resultats_zone1[key].sort()

    # on fait pareil pour calculer la zone 2
    encodings_zone2 = cnn.encode_images(image_dir=f"{dir}/zone2")
    duplicates_zone2 = cnn.find_duplicates(encoding_map=encodings_zone2, min_similarity_threshold=args.similarity)

    resultats_zone2 = {}
    #
    for key, values in duplicates_zone2.items():
        # on crée une liste vide pour y stocker les numéros d'image en int
        liste_doublons = []
        # on ajoute les numéros de chaque image doublons
        for value in values:
            liste_doublons.append(int(value.split(".")[0]))
        # s'il y a des valeurs pour la clé, on conserve l'item, en ajoutant la clé et la liste d'int dans le dictionnaire
        if values:
            resultats_zone2[key] = liste_doublons
            # on ajoute aussi le numero de la clé en int pour pouvoir classer par ordre croissant les images
            resultats_zone2[key].append(int(key.split(".")[0]))
            resultats_zone2[key].sort()

    # pour la zone 3
    encodings_zone3 = cnn.encode_images(image_dir=f"{dir}/zone3")
    duplicates_zone3 = cnn.find_duplicates(encoding_map=encodings_zone3, min_similarity_threshold=args.similarity)


    # # on crée un dictionnaire vide pour stocker le résultat
    resultats_zone3 = {}
    #
    for key, values in duplicates_zone3.items():
        # on crée une liste vide pour y stocker les numéros d'image en int
        liste_doublons = []
        # s'il y a des valeurs pour la clé, on conserve l'item, en ajoutant la clé et la liste d'int dans le dictionnaire
        if values:
            # on ajoute les numéros de chaque image doublons
            for value in values:
                liste_doublons.append(int(value.split(".")[0]))
            resultats_zone3[key] = liste_doublons
            # on ajoute aussi le numero de la clé en int pour pouvoir classer par ordre croissant les images
            resultats_zone3[key].append(int(key.split(".")[0]))
            resultats_zone3[key].sort()
    return resultats_zone1, resultats_zone2, resultats_zone3


def clean_duplicates(zone1, zone2, zone3, nbr_pages):
    """
    Fonction qui supprime les pages en double par jeu de comparaison de couple clé/valeur entre les différents
    dictionnaires
    """
    for key, values in zone1.items():
        for value in values[1:]:
            # on exclut la valeur qui est égale à la clé et les valeurs plus petite que la clé pour ne pas supprimer
            # la mauvaise page
            if str(value) != str(key.split(".")[0]) and int(value) > int(key.split(".")[0]):
                page = value
                if nbr_pages < 100:
                    if value < 10:  # pour que le numero corresponde au numero dans les nom de fichiers du convert_from_path
                        value = ("0" + str(value))
                elif nbr_pages > 100:
                    if value < 10:
                        value = ("00" + str(value))
                    if int(value) <= 99 and int(value) >= 10:
                        value = ("0" + str(value))

                for clef, valeurs in zone2.items():
                    for valeur in valeurs:
                        if clef == f"{page}.png" and str(valeur) == str(key.split(".")[0]):
                            for file in os.listdir(dir):
                                if file.endswith(f"-{value}.png"):
                                    os.remove(f"{dir}/{file}")

                for clef, valeurs in zone3.items():
                    for valeur in valeurs:
                        if clef == f"{page}.png" and str(valeur) == str(key.split(".")[0]):
                            for file in os.listdir(dir):
                                if file.endswith(f"-{value}.png"):
                                    os.remove(f"{dir}/{file}")

    for key, values in zone2.items():
        for value in values[1:]:
            if str(value) != str(key.split(".")[0]) and int(value) > int(key.split(".")[0]):
                page = value
                if nbr_pages < 100:
                    if value < 10:  # pour que le numero corresponde au numero dans les nom de fichiers du convert_from_path
                        value = ("0" + str(value))
                elif nbr_pages > 100:
                    if value < 10:
                        value = ("00" + str(value))
                    if int(value) <= 99 and int(value) >= 10:
                        value = ("0" + str(value))

                for clef, valeurs in zone3.items():
                    for valeur in valeurs:
                        if clef == f"{page}.png" and str(valeur) == str(key.split(".")[0]):
                            for file in os.listdir(dir):
                                if file.endswith(f"-{value}.png"):
                                    os.remove(f"{dir}/{file}")


def recreate_pdf(pdf):
    """Fonction pour reconstruire le pdf après le nettoyage des doublons """
    os.makedirs(args.output, exist_ok=True)
    pdf_name = os.path.basename(pdf)

    dirname = dir
    imgs = []
    for fname in os.listdir(dirname):
        if not fname.endswith(".png"):
            continue
        path = os.path.join(dirname, fname)
        if os.path.isdir(path):
            continue
        imgs.append(path)
    imgs.sort()
    if len(imgs) != nbr_images:
        with open(f"{args.output}/{pdf_name}", "wb") as f:
            f.write(img2pdf.convert(imgs))


if __name__ == '__main__':

    pdfs = glob.glob(f"{args.directory}/*.pdf")
    for pdf in pdfs:
        print(pdf)
        os.makedirs(f"{pdf}_images", exist_ok=True)
        dir = f"{pdf}_images"
        images = convert_from_path(pdf, output_folder=dir, fmt='png')
        nbr_images = len(images)
        crop(images, 'zone1', dir)
        crop(images, 'zone2', dir)
        crop(images, 'zone3', dir)
        resultats1, resultats2, resultats3 = find_duplicates(dir)
        clean_duplicates(resultats1, resultats2, resultats3, nbr_images)
        recreate_pdf(pdf)
