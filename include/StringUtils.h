#pragma once

#include <string>
#include <string_view>

inline std::string MakePascalCase(std::string_view text) {
    std::string result;
    result.reserve(text.size());
    bool capitalizeNext = true;
    for (auto c : text) {
        if (c == ' ') {
            capitalizeNext = true;
            continue;
        }
        if (capitalizeNext) {
            result += std::toupper(c);
            capitalizeNext = false;
        } else {
            result += std::tolower(c);
        }
    }
    return result;
}
