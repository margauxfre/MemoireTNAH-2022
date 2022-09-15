import requests
from lxml import etree
import glob
import re
import json

ns = {'tei': 'http://www.tei-c.org/ns/1.0'}


def clean_text(entry):
    "Function used to remove blank new lines"
    entry = entry.replace("\n", "")
    entry = re.sub('\s{2,}', ' ', entry)
    return entry


def get_data(doc):
    """
    Permet de récupérer les métadonnées souhaitées dans le document XML-TEI
    :param doc: fichier XML à traiter
    :return: un dictionnaire avec le type de métadonnée en clé et son contenu en valeur
    """
    
    data = {}

    # récupération de l'id et du numéro Moreau
    id = doc.xpath("//tei:TEI/@xml:id", namespaces=ns)[0]
    data["id"] = id
    moreau = id.split("_")[0]
    data["numero_Moreau"] = moreau

    # récupération du titre
    bibl = doc.xpath("//tei:TEI//tei:sourceDesc/tei:bibl", namespaces=ns)[0]
    msDesc = doc.xpath("//tei:TEI//tei:msDesc", namespaces=ns)[0]
    titre = clean_text(bibl.xpath("./tei:title/text()", namespaces=ns)[0])
    data["titre"] = titre

    # récupération du lien Google où se trouve le PDF de départ
    urlGoogleBooks = bibl.xpath("./tei:ref/@target", namespaces=ns)[0]
    data["urlGBOOKS"] = urlGoogleBooks

    # récupération des informations sur le lieu de conservation
    ville = msDesc.xpath("./tei:msIdentifier/tei:settlement/text()", namespaces=ns)[0]
    institution = msDesc.xpath("./tei:msIdentifier/tei:institution/text()", namespaces=ns)[0]
    lieu_conservation = institution + " (" + ville + ")"
    data["institution_conservation"] = lieu_conservation
    if msDesc.xpath("./tei:msIdentifier/tei:idno/text()", namespaces=ns):
        cote = msDesc.xpath("./tei:msIdentifier/tei:idno/text()", namespaces=ns)[0]
        data["cote"] = cote

    # récupération de l'auteur
    authors = bibl.xpath("./tei:author", namespaces=ns)
    if authors:
        for author in authors:  # permet de traiter les cas avec plusieurs auteurs
            if author.xpath(".//tei:surname/text()", namespaces=ns) and author.xpath(".//tei:forename/text()",
                                                                                     namespaces=ns):
                surname = author.xpath(".//tei:surname/text()", namespaces=ns)[0]
                forename = author.xpath(".//tei:forename/text()", namespaces=ns)[0]
                _author = surname + ", " + forename
                data["auteur"] = _author
            elif author.xpath("./tei:persName/text()", namespaces=ns) or author.xpath("./tei:orgName/text()",
                                                                                      namespaces=ns):
                _author = author.xpath("./tei:persName/text()", namespaces=ns)[0] or \
                          author.xpath("./tei:orgName/text()", namespaces=ns)[0]
                data["auteur"] = _author
            else:
                pass

    # récupération de l'imprimeur
    publishers = bibl.xpath("./tei:publisher", namespaces=ns)
    if publishers:
        for publisher in publishers:  # permet de traiter les cas avec plusieurs imprimeurs
            if publisher.xpath(".//tei:surname/text()", namespaces=ns) and publisher.xpath(".//tei:forename/text()",
                                                                                           namespaces=ns):
                surname = publisher.xpath(".//tei:surname/text()", namespaces=ns)[0]
                forename = publisher.xpath(".//tei:forename/text()", namespaces=ns)[0]
                _publisher = surname + ", " + forename
                data["imprimeur"] = _publisher
            elif publisher.xpath("./tei:persName/text()!='Sans Nom'", namespaces=ns) or publisher.xpath(
                    "./tei:orgName/text()!='Sans Nom'",
                    namespaces=ns):
                _publisher = publisher.xpath("./tei:persName/text()", namespaces=ns)[0] or \
                             publisher.xpath("./tei:orgName/text()",
                                             namespaces=ns)[0]
                data["imprimeur"] = _publisher
            else:
                pass

    # récupération de la date
    # pour généraliser et uniformiser les manifestes, on ne conserve que l'année d'impression
    # les informations plus précises de datation seront indiquées sur la page dédiée à chaque mazarinade
    date = bibl.xpath("./tei:date", namespaces=ns)[0]
    if date.xpath("./@when"):
        date = date.xpath("./@when")[0][:4]
        data["date"] = date
    elif date.xpath("./@notBefore"):
        date = date.xpath("./@notBefore")[0][:4]
        data["date"] = date
    elif date.xpath("./@notAfter") and not date.xpath("./@notBefore"):
        date = date.xpath("./@notAfter")[0][:4]
        data["date"] = date
    else:
        pass

    # récupération du nombre de pages
    pages = bibl.xpath(".//tei:measure/@quantity", namespaces=ns)[0]
    data["pages"] = pages

    # récupération du format du document
    format = bibl.xpath(".//tei:note/text()", namespaces=ns)[0]
    data["format"] = format
    return data


def create_metadata(info):
    """
    Permet d'ajouter les métadonnées dans un manifeste IIIF
    :param info: dictionnaire contenant les informations récupérées du fichier XML
    :return: manifeste IIIF sous forme de dictionnaire
    """
    # base de manifeste dans lequel on va injecte les valeurs du dictionnaires
    manifeste_json = {
        "@context": "http://iiif.io/api/presentation/3/context.json",
        "id": f"https://antonomaz.huma-num.fr/manifests/{info['numero_Moreau']}.json",
        "type": "Manifest",
        "label": {"fr": [f"{info['titre']}"]},
        "metadata": [],
        "rights": "https://creativecommons.org/licenses/by/3.0/",
        "items": []
    }

    manifeste_json["metadata"].append({
        "label": {"en": ["Title"]},
        "value": {"fr": [f"{info['titre']}"]}
    })
    if 'auteur' in info:
        manifeste_json["metadata"].append({
            "label": {"en": ["Author"]},
            "value": {"fr": [f"{info['auteur']}"]}
        })
    if 'imprimeur' in info:
        manifeste_json["metadata"].append({
            "label": {"en": ["Publisher"]},
            "value": {"fr": [f"{info['imprimeur']}"]}
        })
    if 'date' in info:
        manifeste_json["metadata"].append({
            "label": {"en": ["Date"]},
            "value": {"fr": [f"{info['date']}"]}
        })

    manifeste_json["metadata"].extend(({
                                        "label": {"en": ["Format"]},
                                        "value": {"fr": [f"{info['pages']} p. ; {info['format']}"]}
                                        }, {
                                        "label": {"en": ["Repository"]},
                                        "value": {"fr": [f"{info['institution_conservation']}"]}
                                     }))
    if 'cote' in info:
        manifeste_json["metadata"].append({
            "label": {"en": ["Shelfmark"]},
            "value": {"fr": [f"{info['cote']}"]}
        })

    manifeste_json["metadata"].extend((
                                       {
                                           "label": {"en": ["Language"]},
                                           "value": {"fr": ["Français"]}
                                       }, {
                                           "label": {"en": ["Type"]},
                                           "value": {"fr": ["Imprimé"]}
                                       },  {
                                           "label": {"en": ["Relation"]},
                                           "value": {"fr": [f"{info['numero_Moreau']}"]}
                                       },{
                                           "label": {"en": ["Source Image"]},
                                           "value": {"fr": [f"{info['urlGBOOKS']}"]}
                                       }, {
                                           "label": {"en": ["Digitized by"]},
                                           "value": {"fr": ["Google"]}
                                       }))
    return manifeste_json


def create_canvases(manifest, info):
    """
    Permet de créer un canvas par image dans le manifeste IIIF
    :param manifest: manifeste à traiter
    :param info: dictionnaire contenant les données récupérées des XML
    :return: fichier JSON contenant le manifeste
    """

    pages = {}
    # base d'url si le document contient moins de 10 pages
    # on vérifie si un lien existe
    for i in range(1,10):
        url = f"https://ceres.huma-num.fr/iiif/3/antonomaz--{info['numero_Moreau']}_GBOOKS-00{i}/full/max/0/default.jpg"
        lien = requests.get(url)
        if lien.status_code == 200:
            # si le lien existe, on récupère la taille de l'image
            img_metadata = url.split("/full")[0]
            get_size_img = requests.get(img_metadata)
            size_img = get_size_img.json()
            w = size_img["width"]
            h = size_img["height"]
            pages[url] = {"width": w, "height": h}
    # si 9 pages ont été récupérées, on modifie légèrement l'url et continue pour vérifier l'existence de pages
    # supplémentaires.
    if len(pages) == 9:
        for i in range(10, 100):
            url = f"https://ceres.huma-num.fr/iiif/3/antonomaz--{info['numero_Moreau']}_GBOOKS-0{i}/full/max/0/default.jpg"
            lien = requests.get(url)
            if lien.status_code == 200:
                img_metadata = url.split("/full")[0]
                get_size_img = requests.get(img_metadata)
                size_img = get_size_img.json()
                w = size_img["width"]
                h = size_img["height"]
                pages[url] = {"width": w, "height": h}
            else:
                break
    # idem
    if len(pages) == 99:
        for i in range(100, 1000):
            url = f"https://ceres.huma-num.fr/iiif/3/antonomaz--{info['numero_Moreau']}_GBOOKS-{i}/full/max/0/default.jpg"
            lien = requests.get(url)
            if lien.status_code == 200:
                img_metadata = url.split("/full")[0]
                get_size_img = requests.get(img_metadata)
                size_img = get_size_img.json()
                w = size_img["width"]
                h = size_img["height"]
                pages[url] = {"width": w, "height": h}
            else:
                break
    print(pages)

    nbr_page = 0
    for page in sorted(pages):  # pour chaque page, on crée un canvas avec le lien récupéré
        nbr_page = nbr_page + 1
        lien_image = page.split("/full")[0]
        manifest["items"].append({
      "id": f"{lien_image}",
      "type": "Canvas",
      "label": {
        "en": [
          f"f.{nbr_page}"
        ]
      },
      "height": pages[page]["height"],
      "width": pages[page]["width"],
      "items": [
        {
          "id": f"{lien_image}",
          "type": "AnnotationPage",
          "items": [
            {
              "id": f"{lien_image}",
              "type": "Annotation",
              "motivation": "painting",
              "body": {
                "id": f"{page}",
                "type": "Image",
                "format": "image/jpeg",
                "service": [
                  {
                    "@id": f"{lien_image}",
                    "@type": "ImageService2",
                    "profile": "http://iiif.io/api/image/2/level2.json"
                  }
                ],
                "height": pages[page]["height"],
                "width": pages[page]["width"]
              },
              "target": f"{lien_image}"
            }
          ]
        }
      ]
    })

    # on écrit un fichier JSON en sortie qui correspond au manifeste IIIF
    with open(f"output/{info['numero_Moreau']}.json", "w+") as output:
        manifeste_json = json.dumps(manifest, separators=(",", ":"), indent=2, ensure_ascii=False)
        output.write(manifeste_json)
    return output


if __name__ == "__main__":
    files = glob.glob("./Mazarinades/*.xml", recursive=True)
    for file in files:
        parser = etree.XMLParser(remove_blank_text=True)
        doc = etree.parse(file, parser)
        data = get_data(doc)
        manifest_json = create_metadata(data)
        output = create_canvases(manifest_json, data)

