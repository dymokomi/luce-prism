// Optional independent oracle, linked only by tests against the old C++ core.
#include <kinogaki/Serialize.h>
#include <kinogaki/Compose.h>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
int main(int argc, char** argv) {
    if (argc != 4) return 2;
    std::ifstream input(argv[1], std::ios::binary);
    std::string bytes((std::istreambuf_iterator<char>(input)), {});
    kinogaki::ParseError error;
    std::string mode = argv[3], output;
    auto doc = mode == "compose" ? kinogaki::composeFile(argv[1])
                                 : kinogaki::deserialize(bytes, &error);
    if (!doc) { std::cerr << error.line << ':' << error.column << ' ' << error.message << '\n'; return 1; }
    if (mode == "text") output = kinogaki::serialize(*doc);
    else if (mode == "package") {
        kinogaki::AssetStore assets;
        assets.set(kinogaki::Path("/world/source"), std::string("\0\xff\x01", 3), "application/octet-stream");
        output = kinogaki::serializePackage(*doc, assets);
    } else output = kinogaki::serializeBinary(*doc, mode == "compressed");
    std::ofstream file(argv[2], std::ios::binary);
    file.write(output.data(), static_cast<std::streamsize>(output.size()));
    return file ? 0 : 3;
}
