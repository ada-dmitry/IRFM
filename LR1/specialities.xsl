<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>

    <xsl:key name="k-level" match="object/level" use="."/>
    <xsl:key name="k-level-id" match="object/level-id" use="."/>
    <xsl:key name="k-generation" match="object/generation" use="."/>
    <xsl:key name="k-generation-id" match="object/generation-id" use="."/>
    <xsl:key name="k-type" match="object/type" use="."/>
    <xsl:key name="k-type-id" match="object/type-id" use="."/>

    <xsl:template name="show-not-null">
        <xsl:param name="empty-count"/>
        <xsl:if test="$empty-count = 0">
            <div>Нужен: NOT NULL</div>
        </xsl:if>
    </xsl:template>

    <xsl:template name="sql-not-null">
        <xsl:param name="empty-count"/>
        <xsl:if test="$empty-count = 0">
            <xsl:text> NOT NULL</xsl:text>
        </xsl:if>
    </xsl:template>

    <xsl:template name="sql-check-text">
        <xsl:param name="field-name"/>
        <xsl:param name="items"/>
        <xsl:param name="count"/>
        <xsl:if test="$count &gt;= 2 and $count &lt;= 5">
            <xsl:text> CHECK (</xsl:text>
            <xsl:value-of select="$field-name"/>
            <xsl:text> IN (</xsl:text>
            <xsl:for-each select="$items">
                <xsl:text>'</xsl:text>
                <xsl:value-of select="."/>
                <xsl:text>'</xsl:text>
                <xsl:if test="position() != last()">
                    <xsl:text>, </xsl:text>
                </xsl:if>
            </xsl:for-each>
            <xsl:text>))</xsl:text>
        </xsl:if>
    </xsl:template>

    <xsl:template name="sql-check-int">
        <xsl:param name="field-name"/>
        <xsl:param name="items"/>
        <xsl:param name="count"/>
        <xsl:if test="$count &gt;= 2 and $count &lt;= 5">
            <xsl:text> CHECK (</xsl:text>
            <xsl:value-of select="$field-name"/>
            <xsl:text> IN (</xsl:text>
            <xsl:for-each select="$items">
                <xsl:value-of select="normalize-space(.)"/>
                <xsl:if test="position() != last()">
                    <xsl:text>, </xsl:text>
                </xsl:if>
            </xsl:for-each>
            <xsl:text>))</xsl:text>
        </xsl:if>
    </xsl:template>

    <xsl:template name="field-id">
        <xsl:variable name="empty-count" select="count(objects/object/id[not(normalize-space())])"/>
        <div class="block">
            <div class="field-title">Анализ поля id</div>
            <div>Тип данных: integer</div>
            <div>Число пустых: <xsl:value-of select="$empty-count"/></div>
            <xsl:call-template name="show-not-null"><xsl:with-param name="empty-count" select="$empty-count"/></xsl:call-template>
        </div>
    </xsl:template>

    <xsl:template name="field-name">
        <xsl:variable name="empty-count" select="count(objects/object/name[not(normalize-space())])"/>
        <div class="block">
            <div class="field-title">Анализ поля name</div>
            <div>Тип данных: Текст</div>
            <div>Самый длинный элемент:
                <xsl:for-each select="objects/object/name">
                    <xsl:sort select="string-length(.)" data-type="number" order="descending"/>
                    <xsl:if test="position() = 1"><xsl:value-of select="."/><xsl:text> , длина: </xsl:text><xsl:value-of select="string-length(.)"/></xsl:if>
                </xsl:for-each>
            </div>
            <div>Число пустых: <xsl:value-of select="$empty-count"/></div>
            <xsl:call-template name="show-not-null"><xsl:with-param name="empty-count" select="$empty-count"/></xsl:call-template>
        </div>
    </xsl:template>

    <xsl:template name="field-code">
        <xsl:variable name="empty-count" select="count(objects/object/code[not(normalize-space())])"/>
        <div class="block">
            <div class="field-title">Анализ поля code</div>
            <div>Тип данных: Текст</div>
            <div>Самый длинный элемент:
                <xsl:for-each select="objects/object/code">
                    <xsl:sort select="string-length(.)" data-type="number" order="descending"/>
                    <xsl:if test="position() = 1"><xsl:value-of select="."/><xsl:text> , длина: </xsl:text><xsl:value-of select="string-length(.)"/></xsl:if>
                </xsl:for-each>
            </div>
            <div>Число пустых: <xsl:value-of select="$empty-count"/></div>
            <xsl:call-template name="show-not-null"><xsl:with-param name="empty-count" select="$empty-count"/></xsl:call-template>
        </div>
    </xsl:template>

    <xsl:template name="field-level">
        <xsl:variable name="empty-count" select="count(objects/object/level[not(normalize-space())])"/>
        <div class="block">
            <div class="field-title">Анализ поля level</div>
            <div>Тип данных: Текст</div>
            <div>Самый длинный элемент:
                <xsl:for-each select="objects/object/level">
                    <xsl:sort select="string-length(.)" data-type="number" order="descending"/>
                    <xsl:if test="position() = 1"><xsl:value-of select="."/><xsl:text> , длина: </xsl:text><xsl:value-of select="string-length(.)"/></xsl:if>
                </xsl:for-each>
            </div>
            <div>Число пустых: <xsl:value-of select="$empty-count"/></div>
            <xsl:call-template name="show-not-null"><xsl:with-param name="empty-count" select="$empty-count"/></xsl:call-template>
            <div>Нужен: CHECK (level IN(
                <xsl:for-each select="objects/object/level[generate-id() = generate-id(key('k-level', .)[1])]">
                    <xsl:text> '</xsl:text><xsl:value-of select="."/><xsl:text>' </xsl:text>
                    <xsl:if test="position() != last()"><xsl:text>, </xsl:text></xsl:if>
                </xsl:for-each>
            ))</div>
        </div>
    </xsl:template>

    <xsl:template name="field-level-id">
        <xsl:variable name="empty-count" select="count(objects/object/level-id[not(normalize-space())])"/>
        <div class="block">
            <div class="field-title">Анализ поля level-id</div>
            <div>Тип данных: integer</div>
            <div>Число пустых: <xsl:value-of select="$empty-count"/></div>
            <xsl:call-template name="show-not-null"><xsl:with-param name="empty-count" select="$empty-count"/></xsl:call-template>
            <div>Нужен: CHECK (level_id IN(
                <xsl:for-each select="objects/object/level-id[generate-id() = generate-id(key('k-level-id', .)[1])]">
                    <xsl:text> '</xsl:text><xsl:value-of select="."/><xsl:text>' </xsl:text>
                    <xsl:if test="position() != last()"><xsl:text>, </xsl:text></xsl:if>
                </xsl:for-each>
            ))</div>
        </div>
    </xsl:template>

    <xsl:template name="field-generation">
        <xsl:variable name="empty-count" select="count(objects/object/generation[not(normalize-space())])"/>
        <div class="block">
            <div class="field-title">Анализ поля generation</div>
            <div>Тип данных: Текст</div>
            <div>Самый длинный элемент:
                <xsl:for-each select="objects/object/generation">
                    <xsl:sort select="string-length(.)" data-type="number" order="descending"/>
                    <xsl:if test="position() = 1"><xsl:value-of select="."/><xsl:text> , длина: </xsl:text><xsl:value-of select="string-length(.)"/></xsl:if>
                </xsl:for-each>
            </div>
            <div>Число пустых: <xsl:value-of select="$empty-count"/></div>
            <xsl:call-template name="show-not-null"><xsl:with-param name="empty-count" select="$empty-count"/></xsl:call-template>
            <div>Нужен: CHECK (generation IN(
                <xsl:for-each select="objects/object/generation[generate-id() = generate-id(key('k-generation', .)[1])]">
                    <xsl:text> '</xsl:text><xsl:value-of select="."/><xsl:text>' </xsl:text>
                    <xsl:if test="position() != last()"><xsl:text>, </xsl:text></xsl:if>
                </xsl:for-each>
            ))</div>
        </div>
    </xsl:template>

    <xsl:template name="field-generation-id">
        <xsl:variable name="empty-count" select="count(objects/object/generation-id[not(normalize-space())])"/>
        <div class="block">
            <div class="field-title">Анализ поля generation-id</div>
            <div>Тип данных: integer</div>
            <div>Число пустых: <xsl:value-of select="$empty-count"/></div>
            <xsl:call-template name="show-not-null"><xsl:with-param name="empty-count" select="$empty-count"/></xsl:call-template>
            <div>Нужен: CHECK (generation_id IN(
                <xsl:for-each select="objects/object/generation-id[generate-id() = generate-id(key('k-generation-id', .)[1])]">
                    <xsl:text> '</xsl:text><xsl:value-of select="."/><xsl:text>' </xsl:text>
                    <xsl:if test="position() != last()"><xsl:text>, </xsl:text></xsl:if>
                </xsl:for-each>
            ))</div>
        </div>
    </xsl:template>

    <xsl:template name="field-type">
        <xsl:variable name="empty-count" select="count(objects/object/type[not(normalize-space())])"/>
        <div class="block">
            <div class="field-title">Анализ поля type</div>
            <div>Тип данных: Текст</div>
            <div>Самый длинный элемент:
                <xsl:for-each select="objects/object/type">
                    <xsl:sort select="string-length(.)" data-type="number" order="descending"/>
                    <xsl:if test="position() = 1"><xsl:value-of select="."/><xsl:text> , длина: </xsl:text><xsl:value-of select="string-length(.)"/></xsl:if>
                </xsl:for-each>
            </div>
            <div>Число пустых: <xsl:value-of select="$empty-count"/></div>
            <xsl:call-template name="show-not-null"><xsl:with-param name="empty-count" select="$empty-count"/></xsl:call-template>
            <div>Нужен: CHECK (type IN(
                <xsl:for-each select="objects/object/type[generate-id() = generate-id(key('k-type', .)[1])]">
                    <xsl:text> '</xsl:text><xsl:value-of select="."/><xsl:text>' </xsl:text>
                    <xsl:if test="position() != last()"><xsl:text>, </xsl:text></xsl:if>
                </xsl:for-each>
            ))</div>
        </div>
    </xsl:template>

    <xsl:template name="field-type-id">
        <xsl:variable name="empty-count" select="count(objects/object/type-id[not(normalize-space())])"/>
        <div class="block">
            <div class="field-title">Анализ поля type-id</div>
            <div>Тип данных: integer</div>
            <div>Число пустых: <xsl:value-of select="$empty-count"/></div>
            <xsl:call-template name="show-not-null"><xsl:with-param name="empty-count" select="$empty-count"/></xsl:call-template>
            <div>Нужен: CHECK (type_id IN(
                <xsl:for-each select="objects/object/type-id[generate-id() = generate-id(key('k-type-id', .)[1])]">
                    <xsl:text> '</xsl:text><xsl:value-of select="."/><xsl:text>' </xsl:text>
                    <xsl:if test="position() != last()"><xsl:text>, </xsl:text></xsl:if>
                </xsl:for-each>
            ))</div>
        </div>
    </xsl:template>

    <xsl:template match="/">
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
                <title>Анализ данных файла specialities.xml</title>
                <style type="text/css">
                    body { font-family: Arial, sans-serif; font-size: 16px; line-height: 1.45; background: #ffffff; color: #000000; margin: 24px; }
                    h1 { font-size: 24px; margin: 0 0 18px 0; }
                    h2 { font-size: 20px; margin: 26px 0 10px 0; }
                    .block { margin-bottom: 18px; }
                    .field-title { font-weight: bold; margin-bottom: 4px; }
                    .sql { white-space: pre-wrap; border: 1px solid #bfbfbf; padding: 12px; margin-top: 8px; }
                </style>
            </head>
            <body>
                <h1>Анализ данных файла specialities.xml (specialities.xml)</h1>

                <xsl:call-template name="field-id"/>
                <xsl:call-template name="field-name"/>
                <xsl:call-template name="field-code"/>
                <xsl:call-template name="field-level"/>
                <xsl:call-template name="field-level-id"/>
                <xsl:call-template name="field-generation"/>
                <xsl:call-template name="field-generation-id"/>
                <xsl:call-template name="field-type"/>
                <xsl:call-template name="field-type-id"/>

                <h2>SQL-файл</h2>
                <div class="sql"><xsl:text>DROP TABLE IF EXISTS specialities;
DROP SEQUENCE IF EXISTS specialities_id_seq;

CREATE SEQUENCE specialities_id_seq
    START WITH 1
    INCREMENT BY 1;

CREATE TABLE specialities (
    id INTEGER</xsl:text><xsl:call-template name="sql-not-null"><xsl:with-param name="empty-count" select="count(objects/object/id[not(normalize-space())])"/></xsl:call-template><xsl:text>,

    name VARCHAR(</xsl:text><xsl:for-each select="objects/object/name"><xsl:sort select="string-length(.)" data-type="number" order="descending"/><xsl:if test="position() = 1"><xsl:value-of select="string-length(.)"/></xsl:if></xsl:for-each>
    <xsl:text>)</xsl:text><xsl:call-template name="sql-not-null"><xsl:with-param name="empty-count" select="count(objects/object/name[not(normalize-space())])"/></xsl:call-template><xsl:text>,

    code VARCHAR(</xsl:text><xsl:for-each select="objects/object/code"><xsl:sort select="string-length(.)" data-type="number" order="descending"/><xsl:if test="position() = 1"><xsl:value-of select="string-length(.)"/></xsl:if></xsl:for-each>
    <xsl:text>)</xsl:text><xsl:call-template name="sql-not-null"><xsl:with-param name="empty-count" select="count(objects/object/code[not(normalize-space())])"/></xsl:call-template><xsl:text>,

    level VARCHAR(</xsl:text><xsl:for-each select="objects/object/level"><xsl:sort select="string-length(.)" data-type="number" order="descending"/><xsl:if test="position() = 1"><xsl:value-of select="string-length(.)"/></xsl:if></xsl:for-each>
    <xsl:text>)</xsl:text><xsl:call-template name="sql-not-null"><xsl:with-param name="empty-count" select="count(objects/object/level[not(normalize-space())])"/></xsl:call-template><xsl:call-template name="sql-check-text"><xsl:with-param name="field-name" select="'level'"/><xsl:with-param name="items" select="objects/object/level[generate-id() = generate-id(key('k-level', .)[1])]"/><xsl:with-param name="count" select="count(objects/object/level[generate-id() = generate-id(key('k-level', .)[1])])"/></xsl:call-template><xsl:text>,

    level_id INTEGER</xsl:text><xsl:call-template name="sql-not-null"><xsl:with-param name="empty-count" select="count(objects/object/level-id[not(normalize-space())])"/></xsl:call-template><xsl:call-template name="sql-check-int"><xsl:with-param name="field-name" select="'level_id'"/><xsl:with-param name="items" select="objects/object/level-id[generate-id() = generate-id(key('k-level-id', .)[1])]"/><xsl:with-param name="count" select="count(objects/object/level-id[generate-id() = generate-id(key('k-level-id', .)[1])])"/></xsl:call-template><xsl:text>,

    generation VARCHAR(</xsl:text><xsl:for-each select="objects/object/generation"><xsl:sort select="string-length(.)" data-type="number" order="descending"/><xsl:if test="position() = 1"><xsl:value-of select="string-length(.)"/></xsl:if></xsl:for-each>
    <xsl:text>)</xsl:text><xsl:call-template name="sql-not-null"><xsl:with-param name="empty-count" select="count(objects/object/generation[not(normalize-space())])"/></xsl:call-template><xsl:call-template name="sql-check-text"><xsl:with-param name="field-name" select="'generation'"/><xsl:with-param name="items" select="objects/object/generation[generate-id() = generate-id(key('k-generation', .)[1])]"/><xsl:with-param name="count" select="count(objects/object/generation[generate-id() = generate-id(key('k-generation', .)[1])])"/></xsl:call-template><xsl:text>,

    generation_id INTEGER</xsl:text><xsl:call-template name="sql-not-null"><xsl:with-param name="empty-count" select="count(objects/object/generation-id[not(normalize-space())])"/></xsl:call-template><xsl:call-template name="sql-check-int"><xsl:with-param name="field-name" select="'generation_id'"/><xsl:with-param name="items" select="objects/object/generation-id[generate-id() = generate-id(key('k-generation-id', .)[1])]"/><xsl:with-param name="count" select="count(objects/object/generation-id[generate-id() = generate-id(key('k-generation-id', .)[1])])"/></xsl:call-template><xsl:text>,

    type VARCHAR(</xsl:text><xsl:for-each select="objects/object/type"><xsl:sort select="string-length(.)" data-type="number" order="descending"/><xsl:if test="position() = 1"><xsl:value-of select="string-length(.)"/></xsl:if></xsl:for-each>
    <xsl:text>)</xsl:text><xsl:call-template name="sql-not-null"><xsl:with-param name="empty-count" select="count(objects/object/type[not(normalize-space())])"/></xsl:call-template><xsl:call-template name="sql-check-text"><xsl:with-param name="field-name" select="'type'"/><xsl:with-param name="items" select="objects/object/type[generate-id() = generate-id(key('k-type', .)[1])]"/><xsl:with-param name="count" select="count(objects/object/type[generate-id() = generate-id(key('k-type', .)[1])])"/></xsl:call-template><xsl:text>,

    type_id INTEGER</xsl:text><xsl:call-template name="sql-not-null"><xsl:with-param name="empty-count" select="count(objects/object/type-id[not(normalize-space())])"/></xsl:call-template><xsl:call-template name="sql-check-int"><xsl:with-param name="field-name" select="'type_id'"/><xsl:with-param name="items" select="objects/object/type-id[generate-id() = generate-id(key('k-type-id', .)[1])]"/><xsl:with-param name="count" select="count(objects/object/type-id[generate-id() = generate-id(key('k-type-id', .)[1])])"/></xsl:call-template><xsl:text>,
    CONSTRAINT pk_specialities PRIMARY KEY (id)
);</xsl:text></div>

                <h2>SQL: INSERT-запросы, сформированные из XML</h2>
                <xsl:for-each select="objects/object">
                    <div class="sql"><xsl:text>INSERT INTO specialities (id, name, code, level, level_id, generation, generation_id, type, type_id)
VALUES (
    nextval('specialities_id_seq'),
    '</xsl:text><xsl:value-of select="name"/><xsl:text>',
    '</xsl:text><xsl:value-of select="code"/><xsl:text>',
    '</xsl:text><xsl:value-of select="level"/><xsl:text>',
    </xsl:text><xsl:value-of select="level-id"/><xsl:text>,
    '</xsl:text><xsl:value-of select="generation"/><xsl:text>',
    </xsl:text><xsl:value-of select="generation-id"/><xsl:text>,
    '</xsl:text><xsl:value-of select="type"/><xsl:text>',
    </xsl:text><xsl:value-of select="type-id"/><xsl:text>
);</xsl:text></div>
                </xsl:for-each>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
