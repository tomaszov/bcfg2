<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" >
<xsl:include href="xsl-transform-includes/text-templates.xsl" />
<xsl:output method="xml" indent="no" media-type="text/xml" omit-xml-declaration="yes"/>
<xsl:template match="Report">
<item>
<pubDate><xsl:value-of select="@time" /></pubDate>
<title>BCFG Nightly Statistics</title>
<description>&lt;pre&gt;
Report Run @ <xsl:value-of select="@time" />

Summary:
<xsl:text>    </xsl:text><xsl:value-of select="count(/Report/Node/Statistics/Good)" /> nodes are clean.
<xsl:text>    </xsl:text><xsl:value-of select="count(/Report/Node/Statistics/Bad)" /> nodes are dirty.
<xsl:text>    </xsl:text><xsl:value-of select="count(/Report/Node/Statistics/Modified)" /> nodes were modified in the last run. (includes both good and bad nodes)
<xsl:text>    </xsl:text><xsl:value-of select="count(/Report/Node/Statistics/Stale)" /> nodes did not run this calendar day.
<xsl:text>    </xsl:text><xsl:value-of select="count(/Report/Node/HostInfo[@pingable='N'])" /> nodes were not pingable.
<xsl:text>    </xsl:text>----------------------------
<xsl:text>    </xsl:text><xsl:value-of select="count(/Report/Node)" /> Total<xsl:text>

</xsl:text>


<xsl:if test="count(/Report/Node/Statistics/Good) > 0">
CLEAN:
<xsl:for-each select="Node">
<xsl:sort select="HostInfo/@fqdn"/>
<xsl:if test="count(Statistics/Good) > 0">
<xsl:text>    </xsl:text><xsl:value-of select="HostInfo/@fqdn" /><xsl:text>
</xsl:text>
</xsl:if>
</xsl:for-each><xsl:text>
</xsl:text>
</xsl:if>

<xsl:if test="count(/Report/Node/Statistics/Bad) > 0">
DIRTY:
<xsl:for-each select="Node">
<xsl:sort select="HostInfo/@fqdn"/>
<xsl:if test="count(Statistics/Bad) > 0">
<xsl:text>    </xsl:text><xsl:value-of select="HostInfo/@fqdn" /><xsl:text>
</xsl:text>
</xsl:if>
</xsl:for-each><xsl:text>
</xsl:text>
</xsl:if>
            
<xsl:if test="count(/Report/Node/Statistics/Modified) > 0">
MODIFIED:
<xsl:for-each select="Node">
<xsl:sort select="HostInfo/@fqdn"/>
<xsl:if test="count(Statistics/Modified) > 0">
<xsl:text>    </xsl:text><xsl:value-of select="HostInfo/@fqdn" /><xsl:text>
</xsl:text>
</xsl:if>
</xsl:for-each><xsl:text>
</xsl:text>

</xsl:if>
            
<xsl:if test="count(/Report/Node/Statistics/Stale) > 0">
STALE:
<xsl:for-each select="Node">
<xsl:sort select="HostInfo/@fqdn"/>
<xsl:if test="count(Statistics/Stale) > 0">
<xsl:text>    </xsl:text><xsl:value-of select="HostInfo/@fqdn" /><xsl:text>
</xsl:text>
</xsl:if>
</xsl:for-each><xsl:text>
</xsl:text>

</xsl:if>

<xsl:if test="count(/Report/Node/HostInfo[@pingable='N']) > 0">
UNPINGABLE:
<xsl:for-each select="Node">
<xsl:sort select="HostInfo/@fqdn"/>
<xsl:if test="count(HostInfo[@pingable='N']) > 0">
<xsl:text>    </xsl:text><xsl:value-of select="HostInfo/@fqdn" /><xsl:text>
</xsl:text>
</xsl:if>
</xsl:for-each><xsl:text>
</xsl:text>

</xsl:if>

&lt;/pre&gt;</description>
<link>http://www-unix.mcs.anl.gov/cobalt/bcfg2/index.html</link>
</item>
</xsl:template>
</xsl:stylesheet>