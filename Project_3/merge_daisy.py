import os
import sys
import shutil
import re
from lxml import etree

NS = {
    "oeb": "http://openebook.org/namespaces/oeb-package/1.0/",
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ncx": "http://www.daisy.org/z3986/2005/ncx/",
}


def parse_xml(path):
    parser = etree.XMLParser(remove_blank_text=False, recover=True)
    return etree.parse(path, parser)


def natural_key(s):
    # sort by number within string: part2, part10 -> part2, part10
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def discover_parts(parent_dir):
    parts = []
    for name in sorted(os.listdir(parent_dir), key=natural_key):
        d = os.path.join(parent_dir, name)
        if os.path.isdir(d):
            opf = os.path.join(d, "book.opf")
            ncx = os.path.join(d, "navigation.ncx")
            if os.path.exists(opf) and os.path.exists(ncx):
                parts.append({"dir": d, "opf": opf, "ncx": ncx})
    if not parts:
        raise FileNotFoundError(f"Not found any DAISY chapters in: {parent_dir}")
    return parts


def copy_parts_as_is(parts, out_root):
    for idx, p in enumerate(parts, start=1):
        dst = os.path.join(out_root, "parts", f"part_{idx:02d}")
        print(f"Copy {p['dir']} → {dst}")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(p["dir"], dst)


def read_part_opf_info(part_dir, opf_path):
    root = parse_xml(opf_path).getroot()
    # xác định kiểu OPF của chương (OEB 1.2 hay OPF 2.0)
    ns_uri = root.nsmap.get(None) or ""
    if ns_uri == NS["oeb"]:
        kind = "oeb"
        manifest = root.find(f"{{{NS['oeb']}}}manifest")
        spine = root.find(f"{{{NS['oeb']}}}spine")
        metadata = root.find(f"{{{NS['oeb']}}}metadata")
        item_tag = f"{{{NS['oeb']}}}item"
        itemref_tag = f"{{{NS['oeb']}}}itemref"
    else:
        kind = "opf"
        manifest = root.find(f"{{{NS['opf']}}}manifest")
        spine = root.find(f"{{{NS['opf']}}}spine")
        metadata = root.find(f"{{{NS['opf']}}}metadata")
        item_tag = f"{{{NS['opf']}}}item"
        itemref_tag = f"{{{NS['opf']}}}itemref"

    if manifest is None or spine is None:
        raise ValueError(f"OPF thiếu manifest/spine: {opf_path}")

    return {
        "kind": kind,
        "root": root,
        "manifest": manifest,
        "spine": spine,
        "metadata": metadata,
        "item_tag": item_tag,
        "itemref_tag": itemref_tag,
    }


def build_merged_ncx(parts, out_root):
    ncx_namespace = NS["ncx"]
    ncx = etree.Element(f"{{{ncx_namespace}}}ncx", nsmap={"ncx": NS["ncx"]})
    ncx.set("version", "2005-1")
    head = etree.SubElement(ncx, f"{{{ncx_namespace}}}head")
    for name, content in [
        ("dtb:uid", "uid-merged"),
        ("dtb:depth", "2"),
        ("dtb:totalPageCount", "0"),
        ("dtb:maxPageNumber", "0"),
    ]:
        m = etree.SubElement(head, f"{{{ncx_namespace}}}meta")
        m.set("name", name)
        m.set("content", content)
    docTitle = etree.SubElement(ncx, f"{{{ncx_namespace}}}docTitle")
    etree.SubElement(docTitle, f"{{{ncx_namespace}}}text").text = "Merged"

    navMap = etree.SubElement(ncx, f"{{{ncx_namespace}}}navMap")
    play = 1

    for idx, p in enumerate(parts, start=1):
        pref = f"parts/part_{idx:02d}/"
        src_ncx = parse_xml(p["ncx"]).getroot()
        part_nav = src_ncx.find(f"{{{ncx_namespace}}}navMap")
        if part_nav is None:
            continue

        parent = etree.SubElement(navMap, f"{{{ncx_namespace}}}navPoint")
        parent.set("id", f"part_{idx:02d}")
        parent.set("playOrder", str(play))
        play += 1
        label = etree.SubElement(parent, f"{{{ncx_namespace}}}navLabel")
        etree.SubElement(label, f"{{{ncx_namespace}}}text").text = f"Phần {idx:02d}"
        etree.SubElement(parent, f"{{{ncx_namespace}}}content").set(
            "src", pref + os.path.basename(p["opf"])
        )

        for child in part_nav.findall(f".//{{{ncx_namespace}}}navPoint"):
            new_child = etree.fromstring(etree.tostring(child))
            for e in new_child.iter():
                if e.tag.endswith("navPoint") and e.get("id"):
                    e.set("id", f"p{idx}_{e.get('id')}")
                if e.tag.endswith("content") and e.get("src"):
                    src = e.get("src")
                    base, frag = (src.split("#", 1) + [""])[:2]
                    e.set("src", pref + base + (("#" + frag) if frag else ""))
            for e in new_child.iter():
                if e.tag.endswith("navPoint"):
                    e.set("playOrder", str(play))
                    play += 1
            parent.append(new_child)

    out_path = os.path.join(out_root, "navigation.ncx")
    etree.ElementTree(ncx).write(
        out_path, encoding="utf-8", xml_declaration=True, pretty_print=True
    )
    return out_path


def build_merged_opf(parts, out_root):
    first_info = read_part_opf_info(os.path.dirname(parts[0]["opf"]), parts[0]["opf"])
    kind = first_info["kind"]
    pkg_ns = NS["oeb"] if kind == "oeb" else NS["opf"]

    package = etree.Element(f"{{{pkg_ns}}}package", nsmap={None: pkg_ns})
    package.set("unique-identifier", first_info["root"].get("unique-identifier", "uid"))

    # Copy metadata from the first part
    metadata = etree.SubElement(package, f"{{{pkg_ns}}}metadata")
    if first_info["metadata"] is not None:
        for el in first_info["metadata"]:
            metadata.append(el)

    # manifest + spine
    manifest = etree.SubElement(package, f"{{{pkg_ns}}}manifest")
    spine = etree.SubElement(package, f"{{{pkg_ns}}}spine")

    # Add merged NCX
    ncx_id = "ncx_merged"
    ncx_item = etree.SubElement(manifest, f"{{{pkg_ns}}}item")
    ncx_item.set("id", ncx_id)
    ncx_item.set("href", "navigation.ncx")
    ncx_item.set("media-type", "application/x-dtbncx+xml")
    spine.set("toc", ncx_id)

    # Combine manifests and spines from all parts
    for idx, p in enumerate(parts, start=1):
        pref = f"parts/part_{idx:02d}/"
        info = read_part_opf_info(os.path.dirname(p["opf"]), p["opf"])
        # manifest
        for it in info["manifest"].findall(info["item_tag"]):
            href = it.get("href")
            iid = it.get("id")
            mt = it.get("media-type", "")
            if not href or not iid:
                continue
            if mt == "application/x-dtbncx+xml":
                continue
            new_it = etree.SubElement(manifest, f"{{{pkg_ns}}}item")
            new_it.set("id", f"p{idx}_{iid}")
            new_it.set("href", pref + href.replace("\\", "/"))
            if mt:
                new_it.set("media-type", mt)
            for extra in ("fallback", "properties"):
                if it.get(extra):
                    new_it.set(extra, it.get(extra))
        # spine
        for ir in info["spine"].findall(info["itemref_tag"]):
            idref = ir.get("idref")
            if not idref:
                continue
            etree.SubElement(spine, f"{{{pkg_ns}}}itemref").set(
                "idref", f"p{idx}_{idref}"
            )

    # Save OPF
    out_opf = os.path.join(out_root, "book.opf")
    xml = etree.tostring(
        package, encoding="utf-8", xml_declaration=True, pretty_print=True
    )

    if kind == "oeb":
        doctype = '<!DOCTYPE package PUBLIC "+//ISBN 0-9673008-1-9//DTD OEB 1.2 Package//EN" "http://openebook.org/dtds/oeb-1.2/oebpkg12.dtd">\n'
        with open(out_opf, "wb") as f:
            head, body = xml.split(b"\n", 1) if b"\n" in xml else (xml, b"")
            f.write(head + b"\n" + doctype.encode("utf-8") + body)
    else:
        with open(out_opf, "wb") as f:
            f.write(xml)

    return out_opf


if __name__ == "__main__":
    parent_dir = os.path.abspath(sys.argv[1])
    out_root = os.path.abspath(sys.argv[2])
    parts = discover_parts(parent_dir)
    copy_parts_as_is(parts, out_root)
    build_merged_ncx(parts, out_root)
    build_merged_opf(parts, out_root)
