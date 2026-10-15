// Extract the base-map layers for Kartalar from OpenStreetMap extracts, clipped to the base-map box, in an
// OpenMapTiles-like schema (layer + class), one GeoJSON feature per line per layer file.
//   extract <mask.bin> <outdir> a.osm.pbf [b.osm.pbf ...]
// Detail (buildings, minor roads and paths, residential land use) is kept only where mask.bin is set (Irad and a fringe).
// Build: g++ -O2 -std=c++17 -I libosmium/include -I protozero/include extract.cpp -o extract -lz -lexpat -lbz2 -pthread
#include <osmium/io/any_input.hpp>
#include <osmium/handler.hpp>
#include <osmium/visitor.hpp>
#include <osmium/area/assembler.hpp>
#include <osmium/area/multipolygon_manager.hpp>
#include <osmium/index/map/sparse_mem_array.hpp>
#include <osmium/handler/node_locations_for_ways.hpp>
#include <osmium/relations/relations_manager.hpp>
#include <osmium/geom/geojson.hpp>
#include <osmium/tags/tags_filter.hpp>
#include <cstdio>
#include <cstring>
#include <string>
#include <unordered_set>
#include <vector>
#include <map>

static const double W = 67.5, E = 75.5, S = 40.2, N = 46.5, G = 0.01;
static const int NX = 800, NY = 630;
static std::vector<unsigned char> mask;
static std::map<std::string, FILE*> outs;
static std::string outdir;

static bool in_mask(double lon, double lat) {
    int x = int((lon - W) / G), y = int((lat - S) / G);
    if (x < 0 || y < 0 || x >= NX || y >= NY) return false;
    return mask[size_t(y) * NX + x] != 0;
}
static void emit(const std::string& layer, const std::string& props, const std::string& geom, int minzoom) {
    FILE*& f = outs[layer];
    if (!f) f = fopen((outdir + "/" + layer + ".ndjson").c_str(), "w");
    fprintf(f, "{\"type\":\"Feature\",\"tippecanoe\":{\"layer\":\"%s\",\"minzoom\":%d},\"properties\":{%s},\"geometry\":%s}\n",
            layer.c_str(), minzoom, props.c_str(), geom.c_str());
}
static const char* tag(const osmium::TagList& t, const char* k) { const char* v = t.get_value_by_key(k); return v ? v : ""; }
static bool is(const char* a, const char* b) { return std::strcmp(a, b) == 0; }

struct Bounds { double x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9; int n = 0, inmask = 0; };

static std::string names(const osmium::TagList& t) {
    std::string out;
    for (const char* k : {"name", "name:en", "name:ru", "name:ky", "name:kk", "name:uz"}) {
        const char* v = t.get_value_by_key(k);
        if (!v || !*v) continue;
        std::string key = k; for (auto& ch : key) if (ch == ':') ch = '_';
        std::string e; for (const char* c = v; *c; c++) { if (*c == '"' || *c == '\\') e += '\\'; e += *c; }
        out += ",\"" + key + "\":\"" + e + "\"";
    }
    return out;
}

class Handler : public osmium::handler::Handler {
public:
    osmium::geom::GeoJSONFactory<> fac{6};
    std::unordered_set<osmium::object_id_type> seen_ways, seen_areas;

    template <class NL> Bounds bounds(const NL& nodes) {
        Bounds b;
        for (const auto& nr : nodes) {
            if (!nr.location().valid()) continue;
            double x = nr.location().lon(), y = nr.location().lat();
            b.x0 = std::min(b.x0, x); b.x1 = std::max(b.x1, x); b.y0 = std::min(b.y0, y); b.y1 = std::max(b.y1, y);
            b.n++; if (in_mask(x, y)) b.inmask++;
        }
        return b;
    }
    static bool in_box(const Bounds& b) { return b.n > 0 && b.x1 >= W && b.x0 <= E && b.y1 >= S && b.y0 <= N; }

    void node(const osmium::Node& n) {     // places, for checking the real towns against the lore (not tiled)
        const char* pl = tag(n.tags(), "place");
        const char* nat = tag(n.tags(), "natural");
        std::string kind = pl;
        if (is(nat, "peak") || is(nat, "volcano")) kind = "peak";
        else if (is(tag(n.tags(), "mountain_pass"), "yes") || is(nat, "saddle")) kind = "pass";
        else if (is(nat, "spring")) kind = "spring";
        else if (is(tag(n.tags(), "barrier"), "border_control")) kind = "border";
        else if (is(tag(n.tags(), "aeroway"), "aerodrome")) kind = "aerodrome";
        else if (is(tag(n.tags(), "man_made"), "mineshaft") || is(tag(n.tags(), "man_made"), "adit")) kind = "mine";
        else if (is(nat, "glacier")) kind = "glacier";
        else if (is(pl, "locality") && *tag(n.tags(), "name")) kind = "locality";
        else if (!(is(pl, "city") || is(pl, "town") || is(pl, "village") || is(pl, "hamlet"))) return;
        if (kind != pl && !*tag(n.tags(), "name") && kind != "border" && kind != "aerodrome") return;      // unnamed peaks and passes are no use for labels
        pl = kind.c_str();
        double x = n.location().lon(), y = n.location().lat();
        if (x < W || x > E || y < S || y > N) return;
        auto esc = [](const char* v) { std::string o; for (const char* c = v; *c; c++) { if (*c == '"' || *c == '\\') o += '\\'; o += *c; } return o; };
        char buf[128]; snprintf(buf, sizeof buf, "{\"type\":\"Point\",\"coordinates\":[%.5f,%.5f]}", x, y);
        std::string props = "\"place\":\"" + std::string(pl) + "\"";
        for (const char* k : {"name", "name:en", "name:ru", "name:ky", "name:kk", "name:uz"}) {
            const char* v = tag(n.tags(), k);
            if (*v) { std::string key = k; for (auto& ch : key) if (ch == ':') ch = '_'; props += ",\"" + key + "\":\"" + esc(v) + "\""; }
        }
        props += ",\"population\":\"" + std::string(tag(n.tags(), "population")).substr(0, 10) + "\",\"ele\":\"" + std::string(tag(n.tags(), "ele")).substr(0, 8) + "\",\"id\":" + std::to_string(n.id());
        emit("places", props, buf, 0);
    }

    void way(const osmium::Way& w) {
        const auto& t = w.tags();
        const char* hw = tag(t, "highway"); const char* rw = tag(t, "railway"); const char* ww = tag(t, "waterway"); const char* aw = tag(t, "aeroway");
        if (!*hw && !*rw && !*ww && !is(aw, "runway") && !is(aw, "taxiway")) return;
        if (seen_ways.count(w.id())) return;
        Bounds b = bounds(w.nodes());
        if (!in_box(b) || b.n < 2) return;
        std::string cls, layer = "transportation"; int mz = 0; bool detail = false;
        if (*hw) {
            std::string h = hw; if (h.size() > 5 && h.compare(h.size() - 5, 5, "_link") == 0) h = h.substr(0, h.size() - 5);
            if (h == "motorway") { cls = "motorway"; mz = 4; }
            else if (h == "trunk") { cls = "trunk"; mz = 5; }
            else if (h == "primary") { cls = "primary"; mz = 6; }
            else if (h == "secondary") { cls = "secondary"; mz = 8; }
            else if (h == "tertiary") { cls = "tertiary"; mz = 9; }
            else if (h == "residential" || h == "unclassified" || h == "living_street" || h == "road") { cls = "minor"; mz = 12; detail = (h != "unclassified"); }
            else if (h == "service") { cls = "service"; mz = 13; detail = true; }
            else if (h == "track") { cls = "track"; mz = 13; detail = true; }
            else if (h == "path" || h == "footway" || h == "cycleway" || h == "bridleway" || h == "steps" || h == "pedestrian") { cls = "path"; mz = 14; detail = true; }
            else return;
            if (is(tag(t, "area"), "yes")) return;
        } else if (*rw) {
            if (is(rw, "rail") || is(rw, "narrow_gauge")) { cls = "rail"; mz = 8; if (*tag(t, "service")) { mz = 12; detail = true; } }
            else if (is(rw, "tram") || is(rw, "light_rail")) { cls = "transit"; mz = 12; detail = true; }
            else return;
        } else if (*ww) {
            layer = "waterway";
            if (is(ww, "river")) { cls = "river"; mz = 6; }
            else if (is(ww, "canal")) { cls = "canal"; mz = 9; }
            else if (is(ww, "stream")) { cls = "stream"; mz = 11; }
            else if (is(ww, "ditch") || is(ww, "drain")) { cls = is(ww, "ditch") ? "ditch" : "drain"; mz = 13; detail = true; }
            else return;
        } else {
            layer = "aeroway"; cls = aw; mz = 11;
        }
        if (detail && b.inmask == 0) return;
        std::string props = "\"class\":\"" + cls + "\",\"id\":" + std::to_string(w.id());
        if (layer == "waterway" && (cls == "river" || cls == "canal" || cls == "stream")) props += names(t);
        if (is(tag(t, "bridge"), "yes")) props += ",\"brunnel\":\"bridge\"";
        else if (is(tag(t, "tunnel"), "yes") || is(tag(t, "tunnel"), "culvert")) props += ",\"brunnel\":\"tunnel\"";
        if (is(tag(t, "intermittent"), "yes")) props += ",\"intermittent\":1";
        try { emit(layer, props, fac.create_linestring(w), mz); seen_ways.insert(w.id()); } catch (...) {}
    }

    void area(const osmium::Area& a) {
        const auto& t = a.tags();
        if (seen_areas.count(a.id())) return;
        std::string layer, cls; int mz = 0; bool detail = false;
        const char* nat = tag(t, "natural"); const char* lu = tag(t, "landuse"); const char* le = tag(t, "leisure");
        const char* bd = tag(t, "building"); const char* wwy = tag(t, "waterway"); const char* am = tag(t, "amenity");
        if (is(nat, "water") || is(lu, "reservoir") || is(lu, "basin") || is(wwy, "riverbank")) {
            layer = "water"; cls = (is(tag(t, "water"), "river") || is(wwy, "riverbank")) ? "river" : "lake"; mz = 4;
        } else if (is(nat, "glacier")) { layer = "landcover"; cls = "ice"; mz = 5; }
        else if (is(nat, "wood") || is(lu, "forest")) { layer = "landcover"; cls = "wood"; mz = 7; }
        else if (is(lu, "farmland") || is(lu, "orchard") || is(lu, "vineyard") || is(lu, "plant_nursery") || is(lu, "greenhouse_horticulture")) { layer = "landcover"; cls = "farmland"; mz = 9; }
        else if (is(lu, "grass") || is(lu, "meadow") || is(nat, "grassland") || is(nat, "heath")) { layer = "landcover"; cls = "grass"; mz = 9; }
        else if (is(nat, "scrub")) { layer = "landcover"; cls = "scrub"; mz = 9; }
        else if (is(nat, "sand") || is(nat, "beach") || is(nat, "desert")) { layer = "landcover"; cls = "sand"; mz = 8; }
        else if (is(nat, "bare_rock") || is(nat, "scree")) { layer = "landcover"; cls = "rock"; mz = 9; }
        else if (is(nat, "wetland")) { layer = "landcover"; cls = "wetland"; mz = 9; }
        else if (is(le, "park") || is(le, "garden")) { layer = "park"; cls = "park"; mz = 11; detail = true; }
        else if (is(lu, "residential") || is(lu, "commercial") || is(lu, "industrial") || is(lu, "retail") || is(lu, "cemetery") || is(lu, "military") || is(lu, "railway") || is(lu, "quarry")) {
            layer = "landuse"; cls = lu; mz = 9; detail = true;
        } else if (is(am, "school") || is(am, "university") || is(am, "college") || is(am, "hospital")) { layer = "landuse"; cls = am; mz = 12; detail = true; }
        else if (is(tag(t, "aeroway"), "aerodrome")) { layer = "aeroway"; cls = "aerodrome"; mz = 9; }
        else if (*bd && !is(bd, "no")) { layer = "building"; cls = "building"; mz = 13; detail = true; }
        else return;
        Bounds b;
        for (const auto& outer : a.outer_rings()) { Bounds bb = bounds(outer); b.x0 = std::min(b.x0, bb.x0); b.x1 = std::max(b.x1, bb.x1); b.y0 = std::min(b.y0, bb.y0); b.y1 = std::max(b.y1, bb.y1); b.n += bb.n; b.inmask += bb.inmask; }
        if (!in_box(b)) return;
        if (detail && b.inmask == 0) return;
        std::string props = "\"class\":\"" + cls + "\"";
        if (layer == "water" || (layer == "landcover" && cls == "ice")) props += names(t);
        if (layer == "aeroway" || (layer == "landuse" && (cls == "military" || cls == "quarry" || cls == "industrial"))) {   // for the lore check (curate.py drops them from the tiles)
            props += names(t);
            for (const char* k : {"icao", "iata", "aerodrome:type", "military", "disused", "abandoned"}) { const char* v = tag(t, k); if (*v) { std::string key = k; for (auto& ch : key) if (ch == ':') ch = '_'; props += ",\"" + key + "\":\"" + std::string(v).substr(0, 20) + "\""; } }
        }
        if (layer == "building") { const char* lv = tag(t, "building:levels"); if (*lv) props += ",\"levels\":\"" + std::string(lv).substr(0, 4) + "\""; }
        try { emit(layer, props, fac.create_multipolygon(a), mz); seen_areas.insert(a.id()); } catch (...) {}
    }
};

int main(int argc, char** argv) {
    if (argc < 4) { fprintf(stderr, "usage: extract mask.bin outdir a.pbf [b.pbf ...]\n"); return 1; }
    { FILE* f = fopen(argv[1], "rb"); mask.resize(size_t(NX) * NY); if (fread(mask.data(), 1, mask.size(), f) != mask.size()) return 2; fclose(f); }
    outdir = argv[2];
    Handler h;
    for (int i = 3; i < argc; i++) {
        fprintf(stderr, "reading %s\n", argv[i]);
        osmium::io::File file{argv[i]};
        osmium::area::Assembler::config_type cfg;
        osmium::TagsFilter filter{false};
        for (const char* k : {"natural", "landuse", "leisure", "building", "waterway", "amenity", "aeroway"}) filter.add_rule(true, osmium::TagMatcher{k});
        osmium::area::MultipolygonManager<osmium::area::Assembler> mpm{cfg, filter};
        osmium::relations::read_relations(file, mpm);
        using Index = osmium::index::map::SparseMemArray<osmium::unsigned_object_id_type, osmium::Location>;
        Index index;
        osmium::handler::NodeLocationsForWays<Index> lh{index};
        lh.ignore_errors();
        osmium::io::Reader reader{file, osmium::osm_entity_bits::node | osmium::osm_entity_bits::way | osmium::osm_entity_bits::relation};
        osmium::apply(reader, lh, h, mpm.handler([&h](osmium::memory::Buffer&& buffer) { osmium::apply(buffer, h); }));
        reader.close();
        fprintf(stderr, "  ways so far %zu, areas %zu\n", h.seen_ways.size(), h.seen_areas.size());
    }
    for (auto& kv : outs) fclose(kv.second);
    return 0;
}
