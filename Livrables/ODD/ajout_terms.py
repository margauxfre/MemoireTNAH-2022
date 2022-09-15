# script pour rétablir les éléments term du teiHeader qui ont pu être supprimés lors de corrections antérieures
from lxml import etree

import glob

ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

if __name__ == "__main__":

    files = glob.glob("./Mazarinades/*.xml", recursive=True)
    for file in files:
        parser = etree.XMLParser(remove_blank_text=True)
        doc = etree.parse(file, parser)
        #on récupère le chemin xpath de l'élément parent
        keywords = doc.xpath("//tei:textClass/tei:keywords", namespaces=ns)[0]

        # on définit les éléments à ajouter
        handwritten_note = etree.Element('term',
                                         attrib={"type": "handwritten_note", "subtype": "no"})
        table_of_content = etree.Element('term',
                                         attrib={"type": "table_of_content", "subtype": "no"})
        illustration = etree.Element('term',
                                     attrib={"type": "illustration", "subtype": "no"})

        # on vérifie si les éléments sont présents, sinon on les ajoute
        if not keywords.xpath("./tei:term[@type='handwritten_note']", namespaces=ns):
            keywords.append(handwritten_note)
        if not keywords.xpath("./tei:term[@type='table_of_content']", namespaces=ns):
            keywords.append(table_of_content)
        if not keywords.xpath("./tei:term[@type='illustration']", namespaces=ns):
            keywords.append(illustration)

        # on écrit dans les fichiers
        with open(file, "w+") as sortie_xml:
            output = etree.tostring(doc, pretty_print=True, encoding='utf-8', xml_declaration=True).decode(
                'utf8')
            sortie_xml.write(str(output))
