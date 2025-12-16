#ifndef NODE_H
#define NODE_H

#include <string>
#include <unordered_map>
#include <vector>

struct Node {
    bool is_allowed;
    bool is_suppressed;
    std::unordered_map<std::string, Node*> children;

    Node() : is_allowed(false), is_suppressed(false) {}
    
    ~Node() {
        for (auto& pair : children) {
            delete pair.second;
        }
    }
};

class PolicyEngine {
    Node* root;

public:
    PolicyEngine() {
        root = new Node();
    }

    ~PolicyEngine() {
        delete root;
    }

    void allow_path(const char* path) {
        Node* node = root;
        std::string s(path);
        std::string delimiter = ".";
        size_t pos = 0;
        std::string token;
        
        size_t start = 0;
        size_t end = s.find(delimiter);
        
        while (end != std::string::npos) {
            token = s.substr(start, end - start);
            if (node->children.find(token) == node->children.end()) {
                node->children[token] = new Node();
            }
            node = node->children[token];
            start = end + 1;
            end = s.find(delimiter, start);
        }
        token = s.substr(start);
        if (node->children.find(token) == node->children.end()) {
            node->children[token] = new Node();
        }
        node = node->children[token];
        
        node->is_allowed = true;
    }

    void suppress_path(const char* path) {
        Node* node = root;
        std::string s(path);
        std::string delimiter = ".";
        size_t pos = 0;
        std::string token;
        
        size_t start = 0;
        size_t end = s.find(delimiter);
        
        while (end != std::string::npos) {
            token = s.substr(start, end - start);
            if (node->children.find(token) == node->children.end()) {
                node->children[token] = new Node();
            }
            node = node->children[token];
            start = end + 1;
            end = s.find(delimiter, start);
        }
        token = s.substr(start);
        if (node->children.find(token) == node->children.end()) {
            node->children[token] = new Node();
        }
        node = node->children[token];
        
        node->is_suppressed = true;
    }

    std::string check_access(const char* path) {
        Node* node = root;
        std::string s(path);
        std::string delimiter = ".";
        size_t pos = 0;
        std::string token;
        
        size_t start = 0;
        size_t end = s.find(delimiter);
        
        while (end != std::string::npos) {
            token = s.substr(start, end - start);
            if (node->children.find(token) != node->children.end()) {
                node = node->children[token];
            } else {
                return "DENIED_NOT_FOUND";
            }
            start = end + 1;
            end = s.find(delimiter, start);
        }
        token = s.substr(start);
        if (node->children.find(token) != node->children.end()) {
            node = node->children[token];
        } else {
            return "DENIED_NOT_FOUND";
        }
        
        if (node->is_suppressed) return "BLOCKED_SUPPRESSED";
        if (node->is_allowed) return "ALLOWED";
        return "DENIED_NOT_FOUND";
    }

    // Recursive helper for intersection
    void _intersect_recursive(Node* node_a, Node* node_b, std::string current_path, std::vector<std::string>& results) {
        if (node_a->is_allowed && node_b->is_allowed) {
            results.push_back(current_path);
        }

        for (auto& pair : node_a->children) {
            std::string key = pair.first;
            if (node_b->children.count(key)) {
                std::string next_path = (current_path.empty() ? "" : current_path + ".") + key;
                _intersect_recursive(pair.second, node_b->children[key], next_path, results);
            }
        }
    }

    std::vector<std::string> intersection(PolicyEngine* other) {
        std::vector<std::string> results;
        _intersect_recursive(this->root, other->root, "", results);
        return results;
    }

    // Recursive helper for flattening
    void _flatten_recursive(Node* node, std::string current_path, std::vector<std::string>& results) {
        if (node->is_allowed && !node->is_suppressed) {
            results.push_back(current_path);
        }

        // If suppressed, stop traversal (pruning)
        if (node->is_suppressed) return;

        for (auto& pair : node->children) {
            std::string next_path = (current_path.empty() ? "" : current_path + ".") + pair.first;
            _flatten_recursive(pair.second, next_path, results);
        }
    }

    std::vector<std::string> flatten() {
        std::vector<std::string> results;
        _flatten_recursive(this->root, "", results);
        return results;
    }
};

#endif
