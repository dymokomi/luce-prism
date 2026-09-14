// Optional independent oracle, linked only by tests against the old C++ core.
#include <kinogaki/Serialize.h>
#include <kinogaki/Compose.h>
#include <kinogaki/Codecs.h>
#include <kinogaki/Compute.h>
#include <kinogaki/Logic.h>
#include <kinogaki/Surface.h>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
std::string read(const char* name) {
    std::ifstream input(name, std::ios::binary);
    return std::string((std::istreambuf_iterator<char>(input)), {});
}
int main(int argc, char** argv) {
    if (argc < 4 || argc > 6) return 2;
    std::string bytes = read(argv[1]);
    kinogaki::ParseError error;
    std::string mode = argv[3], output;
    auto inputCodec = mode.starts_with("decode-") ? kinogaki::codecByName(mode.substr(7)) : std::nullopt;
    auto doc = mode == "parse-surface" ? std::optional<kinogaki::Document>(kinogaki::parseSurface(bytes))
             : mode == "compose" ? kinogaki::composeFile(argv[1])
             : inputCodec ? kinogaki::decode(bytes, *inputCodec, &error)
                          : kinogaki::deserialize(bytes, &error);
    if (!doc) { std::cerr << error.line << ':' << error.column << ' ' << error.message << '\n'; return 1; }
    if (mode == "compute") *doc = kinogaki::compute(*doc);
    if (mode == "derive") *doc = kinogaki::derive(*doc);
    if (mode == "overlay" || mode == "diff" || mode == "merge") {
        if (argc < 5) return 2;
        auto other = kinogaki::deserialize(read(argv[4]), &error);
        if (!other) return 1;
        if (mode == "overlay") *doc = kinogaki::overlay(*doc, *other);
        else if (mode == "diff") *doc = kinogaki::diff(*doc, *other);
        else {
            if (argc != 6) return 2;
            auto third = kinogaki::deserialize(read(argv[5]), &error);
            if (!third) return 1;
            auto merged = kinogaki::merge(*doc, *other, *third);
            if (!merged.ok) return 4;
            *doc = std::move(merged.merged);
        }
    }
    if (mode == "serialize-surface") output = kinogaki::serializeSurface(*doc);
    else if (mode.starts_with("encode-")) {
        auto codec = kinogaki::codecByName(mode.substr(7));
        if (!codec) return 2;
        auto encoded = kinogaki::encode(*doc, *codec);
        if (!encoded) return 1;
        output = std::move(*encoded);
    }
    else if (mode == "text") output = kinogaki::serialize(*doc);
    else if ((mode == "package" || mode == "package-empty")) {
        kinogaki::AssetStore assets;
        if (mode == "package") assets.set(kinogaki::Path("/world/source"), std::string("\0\xff\x01", 3), "application/octet-stream");
        output = kinogaki::serializePackage(*doc, assets);
    } else output = kinogaki::serializeBinary(*doc, mode == "compressed");
    std::ofstream file(argv[2], std::ios::binary);
    file.write(output.data(), static_cast<std::streamsize>(output.size()));
    return file ? 0 : 3;
}
