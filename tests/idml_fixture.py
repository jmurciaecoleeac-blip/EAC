"""Construit un IDML minimal à 2 pages pour les tests."""
import zipfile

DESIGNMAP = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" Self="d">
  <idPkg:Graphic src="Resources/Graphic.xml"/>
  <idPkg:Story src="Stories/Story_u10.xml"/>
  <idPkg:Story src="Stories/Story_u11.xml"/>
  <idPkg:Spread src="Spreads/Spread_u1.xml"/>
  <idPkg:Spread src="Spreads/Spread_u2.xml"/>
</Document>"""

GRAPHIC = """<?xml version="1.0" encoding="UTF-8"?>
<idPkg:Graphic xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
  <Color Self="Color/Bleu" Model="Process" Space="RGB" ColorValue="20 60 160"/>
  <Color Self="Color/Jaune" Model="Process" Space="CMYK" ColorValue="0 10 90 0"/>
</idPkg:Graphic>"""

# Page 1 : 400x300 pt. ItemTransform de page : origine spread = (-200, -150)
SPREAD1 = """<?xml version="1.0" encoding="UTF-8"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
 <Spread Self="u1">
  <Page Self="p1" GeometricBounds="0 0 300 400" ItemTransform="1 0 0 1 -200 -150"/>
  <Rectangle Self="r1" FillColor="Color/Jaune" ItemTransform="1 0 0 1 -200 -150">
    <PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
      <PathPointType Anchor="0 0"/><PathPointType Anchor="400 0"/>
      <PathPointType Anchor="400 60"/><PathPointType Anchor="0 60"/>
    </PathPointArray></GeometryPathType></PathGeometry>
  </Rectangle>
  <Rectangle Self="r2" Name="{{photo}}" ItemTransform="1 0 0 1 -180 -60">
    <PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
      <PathPointType Anchor="0 0"/><PathPointType Anchor="180 0"/>
      <PathPointType Anchor="180 120"/><PathPointType Anchor="0 120"/>
    </PathPointArray></GeometryPathType></PathGeometry>
    <Image Self="img1"><Link Self="l1" LinkResourceURI="file:/Users/x/photo.jpg"/></Image>
  </Rectangle>
  <TextFrame Self="tf1" Name="{{titre}}" ParentStory="u10" ItemTransform="1 0 0 1 -190 -140">
    <PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
      <PathPointType Anchor="0 0"/><PathPointType Anchor="380 0"/>
      <PathPointType Anchor="380 40"/><PathPointType Anchor="0 40"/>
    </PathPointArray></GeometryPathType></PathGeometry>
  </TextFrame>
 </Spread>
</idPkg:Spread>"""

SPREAD2 = """<?xml version="1.0" encoding="UTF-8"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
 <Spread Self="u2">
  <Page Self="p2" GeometricBounds="0 0 300 400" ItemTransform="1 0 0 1 -200 -150"/>
  <TextFrame Self="tf2" ParentStory="u11" ItemTransform="1 0 0 1 -180 -100">
    <PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
      <PathPointType Anchor="0 0"/><PathPointType Anchor="360 0"/>
      <PathPointType Anchor="360 150"/><PathPointType Anchor="0 150"/>
    </PathPointArray></GeometryPathType></PathGeometry>
  </TextFrame>
 </Spread>
</idPkg:Spread>"""

STORY10 = """<?xml version="1.0" encoding="UTF-8"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
 <Story Self="u10">
  <ParagraphStyleRange Justification="CenterAlign">
   <CharacterStyleRange PointSize="24" FillColor="Color/Bleu" AppliedFont="DejaVu Sans" FontStyle="Bold">
    <Content>Titre par défaut</Content>
   </CharacterStyleRange>
  </ParagraphStyleRange>
 </Story>
</idPkg:Story>"""

STORY11 = """<?xml version="1.0" encoding="UTF-8"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
 <Story Self="u11">
  <ParagraphStyleRange>
   <CharacterStyleRange PointSize="14" AppliedFont="DejaVu Sans">
    <Content>Bienvenue {{prenom}}, ceci est un long paragraphe destiné à vérifier la césure automatique dans le bloc de texte.</Content>
    <Br/>
    <Content>Deuxième paragraphe.</Content>
   </CharacterStyleRange>
  </ParagraphStyleRange>
 </Story>
</idPkg:Story>"""


def build(path: str) -> str:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        zf.writestr("designmap.xml", DESIGNMAP)
        zf.writestr("Resources/Graphic.xml", GRAPHIC)
        zf.writestr("Spreads/Spread_u1.xml", SPREAD1)
        zf.writestr("Spreads/Spread_u2.xml", SPREAD2)
        zf.writestr("Stories/Story_u10.xml", STORY10)
        zf.writestr("Stories/Story_u11.xml", STORY11)
    return path


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "test.idml")
