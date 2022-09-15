# script pour rassembler les deux éléments note et target faisant référence aux notices de la
# bibliothèque Mazarine en un élément relatedItem

from lxml import etree
import glob

ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

if __name__ == "__main__":

    files = glob.glob("../Mazarinades/**/*.xml", recursive=True)
    output = []
    for file in files:
        parser = etree.XMLParser(remove_blank_text=True)
        doc = etree.parse(file, parser)
        # on crée un élément relatedItem avec les attributs souhaités
        relatedItem = etree.Element('relatedItem',
                                    attrib={"source": "", "type": "identifer", "subtype": "", "cert": "",
                                            "target": ""})

        # on sélectionne les éléments sur lesquels on va travailler
        bibl = doc.xpath('//tei:teiHeader//tei:sourceDesc/tei:bibl', namespaces=ns)[0]
        note = bibl.xpath('./tei:note[2]', namespaces=ns)[0]
        cert = note.xpath('./@cert', namespaces=ns)[0]
        
        # pour sélectionner le text() quand il y en a un
        try:
            identifier = note.xpath('./text()')[0]
        except:
            identifier = 'none'
            
        # pour sélectionner le ref et son @target quand il y en a un
        try:
            ref = bibl.xpath('./tei:ref[2]', namespaces=ns)[0]
            target = ref.xpath('./@target', namespaces=ns)[0]

        except:
            target = 'none'
            # certains anciens fichiers sans notice ayant un @cert='high', on le corrige
            cert = 'low'

        # harmonisation de la valeur de target quand il n'y a pas de lien
        if target == '#URLSource':
            target = 'none'
            cert = 'low'
        if target == 'sans notice':
            target = 'none'

        # on ajoute le nouvel élément à la fin du bibl
        bibl.append(relatedItem)
        # on lui assigne les valeurs d'attributs
        relatedItem.attrib['source'] = 'Mazarine'
        relatedItem.attrib['type'] = 'identifier'
        relatedItem.attrib['cert'] = cert
        relatedItem.attrib['subtype'] = identifier
        relatedItem.attrib['target'] = target

        # une fois fois les valeurs récupérées, on supprime les deux éléments qui ne sont plus utilisés dans l'ODD
        bibl.remove(note)
        try:
            bibl.remove(ref)
        except:
            pass

        # on écrit dans les fichiers
        with open(file, "w+") as sortie_xml:
            output = etree.tostring(doc, pretty_print=True, encoding='utf-8', xml_declaration=True).decode(
                'utf8')
            sortie_xml.write(str(output))
