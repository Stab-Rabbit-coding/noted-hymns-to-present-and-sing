#!/usr/bin/env python3
"""
generate_templates.py — Build blank presentation template files for hymn slides.

Outputs (written to the same directory as this script):
    Hymn_Slide_Template.potx   — PowerPoint template (OOXML)
    Hymn_Slide_Template.otp    — LibreOffice Impress template (ODF)

Both templates use:
    Melody text box  — Musiqwik font, 28 pt, gold (#F0E68C), upper third
    Lyrics text box  — OpenDyslexic Mono font, 32 pt, white (#E4E4E4), lower 2/3
    Background       — dark navy (#1A1A2E)

Usage:
    python3 templates/generate_templates.py

Re-run whenever the layout or font choices change.
"""

import io
import zipfile
from pathlib import Path

HERE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Shared colour palette (matches hymn_to_presentation.py)
# ---------------------------------------------------------------------------
BG    = "1A1A2E"
GOLD  = "F0E68C"
WHITE = "E4E4E4"

# ---------------------------------------------------------------------------
# Slide dimensions (EMU)  —  9 144 000 × 5 143 500  ≈  10 × 5.625 in  (16:9)
# matches hymn_to_presentation.py
# ---------------------------------------------------------------------------
W = 9_144_000
H = 5_143_500

# Margins and box geometry (EMU)
MX = int(W * 0.06)   # 548 640  ≈ 0.6 in
MY = int(H * 0.08)   # 411 480  ≈ 0.45 in

# Melody box  (top third)
MEL_X  = MX
MEL_Y  = MY
MEL_CX = W - 2 * MX
MEL_CY = int(H * 0.28)

# Lyrics box  (lower ~60 %)
LYR_X  = MX
LYR_Y  = int(H * 0.38)
LYR_CX = W - 2 * MX
LYR_CY = int(H * 0.58)

# Font sizes in hundredths of a point (OOXML) / direct pt values (ODF)
MEL_SZ = 2800   # 28 pt in OOXML hundredths
LYR_SZ = 3200   # 32 pt
MEL_PT = 28     # for ODF
LYR_PT = 32


# ===========================================================================
# PowerPoint template  (.potx)
# ===========================================================================

def _potx_content_types() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels"
    ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.template.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <Override PartName="/docProps/core.xml"
    ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml"
    ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""


def _potx_rels() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="ppt/presentation.xml"/>
  <Relationship Id="rId2"
    Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
    Target="docProps/core.xml"/>
  <Relationship Id="rId3"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties"
    Target="docProps/app.xml"/>
</Relationships>"""


def _potx_app() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>noted-hymns-to-present-and-sing</Application>
  <PresentationFormat>Widescreen</PresentationFormat>
  <Slides>0</Slides>
</Properties>"""


def _potx_core() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties
  xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Hymn Slide Template</dc:title>
  <dc:subject>Hymn slides — MusiQwik melody + OpenDyslexic Mono lyrics</dc:subject>
  <dc:creator>noted-hymns-to-present-and-sing</dc:creator>
  <dcterms:created xsi:type="dcterms:W3CDTF">2026-06-28T00:00:00Z</dcterms:created>
</cp:coreProperties>"""


def _potx_presentation() -> str:
    return f"""\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  saveSubsetFonts="1">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldSz cx="{W}" cy="{H}" type="custom"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle>
    <a:defPPr><a:defRPr lang="en-US"/></a:defPPr>
  </p:defaultTextStyle>
</p:presentation>"""


def _potx_presentation_rels() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster"
    Target="slideMasters/slideMaster1.xml"/>
  <Relationship Id="rId2"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"
    Target="theme/theme1.xml"/>
</Relationships>"""


def _potx_theme() -> str:
    return f"""\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Hymn">
  <a:themeElements>
    <a:clrScheme name="Hymn">
      <a:dk1><a:srgbClr val="000000"/></a:dk1>
      <a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="{BG}"/></a:dk2>
      <a:lt2><a:srgbClr val="{WHITE}"/></a:lt2>
      <a:accent1><a:srgbClr val="{GOLD}"/></a:accent1>
      <a:accent2><a:srgbClr val="C0504D"/></a:accent2>
      <a:accent3><a:srgbClr val="9BBB59"/></a:accent3>
      <a:accent4><a:srgbClr val="8064A2"/></a:accent4>
      <a:accent5><a:srgbClr val="4BACC6"/></a:accent5>
      <a:accent6><a:srgbClr val="F79646"/></a:accent6>
      <a:hlink><a:srgbClr val="0000FF"/></a:hlink>
      <a:folHlink><a:srgbClr val="800080"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Hymn">
      <a:majorFont>
        <a:latin typeface="Musiqwik"/>
        <a:ea typeface=""/><a:cs typeface=""/>
      </a:majorFont>
      <a:minorFont>
        <a:latin typeface="OpenDyslexic Mono"/>
        <a:ea typeface=""/><a:cs typeface=""/>
      </a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Hymn">
      <a:fillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:gradFill rotWithShape="1">
          <a:gsLst>
            <a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="50000"/></a:schemeClr></a:gs>
            <a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="50000"/></a:schemeClr></a:gs>
          </a:gsLst>
          <a:lin ang="16200000" scaled="0"/>
        </a:gradFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:fillStyleLst>
      <a:lnStyleLst>
        <a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
        <a:ln w="25400"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
        <a:ln w="38100"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
      </a:lnStyleLst>
      <a:effectStyleLst>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
      </a:effectStyleLst>
      <a:bgFillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>"""


def _potx_slide_master() -> str:
    return f"""\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld>
    <p:bg>
      <p:bgPr>
        <a:solidFill><a:srgbClr val="{BG}"/></a:solidFill>
      </p:bgPr>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2"
    accent1="accent1" accent2="accent2" accent3="accent3"
    accent4="accent4" accent5="accent5" accent6="accent6"
    hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rId1"/>
  </p:sldLayoutIdLst>
  <p:txStyles>
    <p:titleStyle>
      <a:lvl1pPr>
        <a:defRPr sz="{MEL_SZ}">
          <a:solidFill><a:srgbClr val="{GOLD}"/></a:solidFill>
          <a:latin typeface="Musiqwik"/>
        </a:defRPr>
      </a:lvl1pPr>
    </p:titleStyle>
    <p:bodyStyle>
      <a:lvl1pPr>
        <a:defRPr sz="{LYR_SZ}">
          <a:solidFill><a:srgbClr val="{WHITE}"/></a:solidFill>
          <a:latin typeface="OpenDyslexic Mono"/>
        </a:defRPr>
      </a:lvl1pPr>
    </p:bodyStyle>
    <p:otherStyle>
      <a:defPPr><a:defRPr lang="en-US"/></a:defPPr>
    </p:otherStyle>
  </p:txStyles>
</p:sldMaster>"""


def _potx_slide_master_rels() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
    Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"
    Target="../theme/theme1.xml"/>
</Relationships>"""


def _potx_slide_layout() -> str:
    return f"""\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  type="blank" preserve="1">
  <p:cSld name="Hymn Slide">
    <p:bg>
      <p:bgPr>
        <a:solidFill><a:srgbClr val="{BG}"/></a:solidFill>
      </p:bgPr>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>

      <!-- Melody text box: Musiqwik font, upper area -->
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Melody"/>
          <p:cNvSpPr txBox="1"><a:spLocks noGrp="1"/></p:cNvSpPr>
          <p:nvPr/>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm>
            <a:off x="{MEL_X}" y="{MEL_Y}"/>
            <a:ext cx="{MEL_CX}" cy="{MEL_CY}"/>
          </a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          <a:noFill/>
        </p:spPr>
        <p:txBody>
          <a:bodyPr wrap="square" rtlCol="0"/>
          <a:lstStyle>
            <a:lvl1pPr algn="l">
              <a:defRPr sz="{MEL_SZ}" dirty="0">
                <a:solidFill><a:srgbClr val="{GOLD}"/></a:solidFill>
                <a:latin typeface="Musiqwik"/>
              </a:defRPr>
            </a:lvl1pPr>
          </a:lstStyle>
          <a:p>
            <a:r>
              <a:rPr lang="en-US" dirty="0"/>
              <a:t>Melody (paste MusiQwik characters here)</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>

      <!-- Lyrics text box: OpenDyslexic Mono, lower area -->
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="3" name="Lyrics"/>
          <p:cNvSpPr txBox="1"><a:spLocks noGrp="1"/></p:cNvSpPr>
          <p:nvPr/>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm>
            <a:off x="{LYR_X}" y="{LYR_Y}"/>
            <a:ext cx="{LYR_CX}" cy="{LYR_CY}"/>
          </a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          <a:noFill/>
        </p:spPr>
        <p:txBody>
          <a:bodyPr wrap="square" rtlCol="0"/>
          <a:lstStyle>
            <a:lvl1pPr algn="l">
              <a:defRPr sz="{LYR_SZ}" dirty="0">
                <a:solidFill><a:srgbClr val="{WHITE}"/></a:solidFill>
                <a:latin typeface="OpenDyslexic Mono"/>
              </a:defRPr>
            </a:lvl1pPr>
          </a:lstStyle>
          <a:p>
            <a:r>
              <a:rPr lang="en-US" dirty="0"/>
              <a:t>Lyrics (paste OpenDyslexic Mono text here)</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>

    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""


def _potx_slide_layout_rels() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster"
    Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""


def make_potx(out: Path) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml",                    _potx_content_types())
        zf.writestr("_rels/.rels",                            _potx_rels())
        zf.writestr("docProps/app.xml",                       _potx_app())
        zf.writestr("docProps/core.xml",                      _potx_core())
        zf.writestr("ppt/presentation.xml",                   _potx_presentation())
        zf.writestr("ppt/_rels/presentation.xml.rels",        _potx_presentation_rels())
        zf.writestr("ppt/theme/theme1.xml",                   _potx_theme())
        zf.writestr("ppt/slideMasters/slideMaster1.xml",      _potx_slide_master())
        zf.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels",
                    _potx_slide_master_rels())
        zf.writestr("ppt/slideLayouts/slideLayout1.xml",      _potx_slide_layout())
        zf.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels",
                    _potx_slide_layout_rels())
    out.write_bytes(buf.getvalue())
    print(f"Written: {out}")


# ===========================================================================
# LibreOffice Impress template  (.otp)
# ===========================================================================

# Slide dimensions in centimetres for ODF
# 9144000 EMU / 914400 EMU·cm⁻¹ = 10 cm  — but ODF uses 1/100 mm units
# 9144000 / 36000 = 254.00 (tenths of mm) → 25.4 cm
# 5143500 / 36000 = 142.875 → 14.29 cm (rounded)
SLIDE_W_CM = "25.4cm"
SLIDE_H_CM = "14.29cm"

# Box geometry in cm  (EMU / 914400 * 2.54 → cm)
def _emu_to_cm(emu: int) -> str:
    return f"{emu / 914400 * 2.54:.3f}cm"


MEL_X_CM  = _emu_to_cm(MEL_X)
MEL_Y_CM  = _emu_to_cm(MEL_Y)
MEL_CX_CM = _emu_to_cm(MEL_CX)
MEL_CY_CM = _emu_to_cm(MEL_CY)

LYR_X_CM  = _emu_to_cm(LYR_X)
LYR_Y_CM  = _emu_to_cm(LYR_Y)
LYR_CX_CM = _emu_to_cm(LYR_CX)
LYR_CY_CM = _emu_to_cm(LYR_CY)


def _otp_mimetype() -> bytes:
    return b"application/vnd.oasis.opendocument.presentation-template"


def _otp_manifest() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest
  xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
  manifest:version="1.3">
  <manifest:file-entry manifest:full-path="/"
    manifest:media-type="application/vnd.oasis.opendocument.presentation-template"
    manifest:version="1.3"/>
  <manifest:file-entry manifest:full-path="content.xml"
    manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="meta.xml"
    manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="settings.xml"
    manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="styles.xml"
    manifest:media-type="text/xml"/>
</manifest:manifest>"""


def _otp_meta() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  office:version="1.3">
  <office:meta>
    <meta:generator>noted-hymns-to-present-and-sing/generate_templates.py</meta:generator>
    <dc:title>Hymn Slide Template</dc:title>
    <dc:subject>Hymn slides — MusiQwik melody + OpenDyslexic Mono lyrics</dc:subject>
    <meta:creation-date>2026-06-28T00:00:00</meta:creation-date>
  </office:meta>
</office:document-meta>"""


def _otp_settings() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8"?>
<office:document-settings
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"
  office:version="1.3">
  <office:settings>
    <config:config-item-set config:name="ooo:view-settings">
      <config:config-item config:name="VisibleAreaTop" config:type="int">0</config:config-item>
      <config:config-item config:name="VisibleAreaLeft" config:type="int">0</config:config-item>
    </config:config-item-set>
  </office:settings>
</office:document-settings>"""


def _otp_styles() -> str:
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
  xmlns:presentation="urn:oasis:names:tc:opendocument:xmlns:presentation:1.0"
  office:version="1.3">

  <office:styles>
    <!-- Master page background -->
    <style:style style:name="HymnMasterPage" style:family="drawing-page">
      <style:drawing-page-properties
        draw:fill="solid"
        draw:fill-color="#{BG}"
        draw:background-size="border"
        presentation:display-header="false"
        presentation:display-footer="false"
        presentation:display-page-number="false"
        presentation:display-date-time="false"/>
    </style:style>

    <!-- Melody paragraph style -->
    <style:style style:name="MelodyParagraph" style:family="paragraph">
      <style:paragraph-properties fo:text-align="left" fo:margin-left="0cm"/>
      <style:text-properties
        fo:font-family="Musiqwik"
        fo:font-size="{MEL_PT}pt"
        fo:color="#{GOLD}"/>
    </style:style>

    <!-- Lyrics paragraph style -->
    <style:style style:name="LyricsParagraph" style:family="paragraph">
      <style:paragraph-properties fo:text-align="left" fo:margin-left="0cm"/>
      <style:text-properties
        fo:font-family="OpenDyslexic Mono"
        fo:font-size="{LYR_PT}pt"
        fo:color="#{WHITE}"/>
    </style:style>
  </office:styles>

  <office:master-styles>
    <style:master-page
      style:name="Default"
      style:display-name="Default Layout"
      draw:style-name="HymnMasterPage">
    </style:master-page>
  </office:master-styles>
</office:document-styles>"""


def _otp_content() -> str:
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:presentation="urn:oasis:names:tc:opendocument:xmlns:presentation:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  office:version="1.3">

  <office:automatic-styles>
    <!-- Slide page style -->
    <style:style style:name="dp1" style:family="drawing-page">
      <style:drawing-page-properties
        draw:fill="solid"
        draw:fill-color="#{BG}"
        draw:background-size="border"
        presentation:display-header="false"
        presentation:display-footer="false"
        presentation:display-page-number="false"
        presentation:display-date-time="false"/>
    </style:style>

    <!-- Melody frame graphic style -->
    <style:style style:name="gr-melody" style:family="graphic">
      <style:graphic-properties
        draw:fill="none"
        draw:stroke="none"
        fo:wrap-option="wrap"/>
    </style:style>

    <!-- Lyrics frame graphic style -->
    <style:style style:name="gr-lyrics" style:family="graphic">
      <style:graphic-properties
        draw:fill="none"
        draw:stroke="none"
        fo:wrap-option="wrap"/>
    </style:style>
  </office:automatic-styles>

  <office:body>
    <office:presentation>
      <draw:page
        draw:name="Hymn Slide"
        draw:style-name="dp1"
        draw:master-page-name="Default">

        <!-- Melody frame: Musiqwik font, upper area -->
        <draw:frame
          draw:style-name="gr-melody"
          draw:name="Melody"
          draw:layer="layout"
          svg:width="{MEL_CX_CM}"
          svg:height="{MEL_CY_CM}"
          svg:x="{MEL_X_CM}"
          svg:y="{MEL_Y_CM}">
          <draw:text-box>
            <text:p text:style-name="MelodyParagraph">Melody (paste MusiQwik characters here)</text:p>
          </draw:text-box>
        </draw:frame>

        <!-- Lyrics frame: OpenDyslexic Mono, lower area -->
        <draw:frame
          draw:style-name="gr-lyrics"
          draw:name="Lyrics"
          draw:layer="layout"
          svg:width="{LYR_CX_CM}"
          svg:height="{LYR_CY_CM}"
          svg:x="{LYR_X_CM}"
          svg:y="{LYR_Y_CM}">
          <draw:text-box>
            <text:p text:style-name="LyricsParagraph">Lyrics (paste OpenDyslexic Mono text here)</text:p>
          </draw:text-box>
        </draw:frame>

      </draw:page>
    </office:presentation>
  </office:body>
</office:document-content>"""


def make_otp(out: Path) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # mimetype must be first and stored (not compressed) per ODF spec
        zf.writestr(
            zipfile.ZipInfo("mimetype"), _otp_mimetype(),
            compress_type=zipfile.ZIP_STORED,
        )
        zf.writestr("META-INF/manifest.xml", _otp_manifest())
        zf.writestr("meta.xml",              _otp_meta())
        zf.writestr("settings.xml",          _otp_settings())
        zf.writestr("styles.xml",            _otp_styles())
        zf.writestr("content.xml",           _otp_content())
    out.write_bytes(buf.getvalue())
    print(f"Written: {out}")


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    make_potx(HERE / "Hymn_Slide_Template.potx")
    make_otp(HERE  / "Hymn_Slide_Template.otp")
    print("Done.  Open the template files in PowerPoint or LibreOffice Impress.")
    print("Both fonts (Musiqwik and OpenDyslexic Mono) must be installed first;")
    print("see docs/fonts.md for installation instructions.")
