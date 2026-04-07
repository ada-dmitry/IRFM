from lxml import etree

xml = etree.parse("specialities.xml")

xslt = etree.parse("specialities.xsl")

transform = etree.XSLT(xslt)

result = transform(xml)

with open("specialities.html", "wb") as f:
    f.write(etree.tostring(result, pretty_print=True, encoding="UTF-8"))

print("HTML успешно создан: specialities.html")
