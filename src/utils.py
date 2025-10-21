#from __future__ import annotations
import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Iterable, Dict, Optional
import json

def single_quote_to_double_with_content(str_in) -> str:
    """
    A function to parse a string and convert it into a valid JSON format.
    It replaces single quotes with double quotes
    """
    # Replace single quotes with double quotes except when they are inside double quotes.
    opend = False
    opend_content = False
    str_out = ""
    for i, c in enumerate(str_in):
        if c != "'":
            if c == '"' and not opend:
                opend = True
            elif c == '"' and opend:
                opend = False
            elif c == "c" and i + len('ontent') < len(str_in) and str_in[i:i + len('ontent')+1] == "content":
                opend_content = True
            elif c == "t" and i - len('content') >= 0 and str_in[i - len('content'):i + 1] == "content":
                opend_content = False

            if opend_content and c == '"':
                str_out += '\\"'
            else:
                str_out += c

        else:
            if opend:
                str_out += c
            else:
                str_out += '"'
    return str_out

def single_quote_to_double(str_in) -> str:
    """
    A function to parse a string and convert it into a valid JSON format.
    It replaces single quotes with double quotes
    """
    # Replace single quotes with double quotes except when they are inside double quotes.
    opend = False
    str_out = ""
    for c in str_in:
        if c != "'":
            if c == '"' and not opend:
                opend = True
            elif c == '"' and opend:
                opend = False
            str_out += c
        else:
            if opend:
                str_out += c
            else:
                str_out += '"'
    
  
    
    return str_out

def to_dict(obj):
    return json.loads(json.dumps(obj, default=lambda o: o.__dict__))


TEST = """{'folders': [{'name': 'user_service', 'folders': [{'name': 'src', 'folders': [{'name': 'main', 'folders': [{'name': 'java', 'folders': [{'name': 'com', 'folders': [{'name': 'example', 'folders': [{'name': 'userservice', 'folders': [{'name': 'controller', 'folders': [], 'files': [{'name': 'UserController.java', 'content': 'package com.example.userservice.controller;\n\nimport com.example.userservice.model.User;\nimport com.example.userservice.service.UserService;\nimport org.springframework.beans.factory.annotation.Autowired;\nimport org.springframework.http.ResponseEntity;\nimport org.springframework.web.bind.annotation.*;\nimport java.util.List;\n\n@RestController\n@RequestMapping("/users")\npublic class UserController {\n    @Autowired\n    private UserService userService;\n\n    @GetMapping\n    public List<User> getAllUsers() {\n        return userService.getAllUsers();\n    }\n\n    @GetMapping("/{id}")\n    public ResponseEntity<User> getUserById(@PathVariable Long id) {\n        User user = userService.getUserById(id);\n        if (user != null) {\n            return ResponseEntity.ok(user);\n        } else {\n            return ResponseEntity.notFound().build();\n        }\n    }\n\n    @PostMapping\n    public User createUser(@RequestBody User user) {\n        return userService.createUser(user);\n    }\n\n    @PutMapping("/{id}")\n    public ResponseEntity<User> updateUser(@PathVariable Long id, @RequestBody User user) {\n        User updatedUser = userService.updateUser(id, user);\n        if (updatedUser != null) {\n            return ResponseEntity.ok(updatedUser);\n        } else {\n            return ResponseEntity.notFound().build();\n        }\n    }\n\n    @DeleteMapping("/{id}")\n    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {\n        if (userService.deleteUser(id)) {\n            return ResponseEntity.noContent().build();\n        } else {\n            return ResponseEntity.notFound().build();\n        }\n    }\n}\n'}]}, {'name': 'model', 'folders': [], 'files': [{'name': 'User.java', 'content': 'package com.example.userservice.model;\n\nimport javax.persistence.*;\n\n@Entity\n@Table(name = "users")\npublic class User {\n    @Id\n    @GeneratedValue(strategy = GenerationType.IDENTITY)\n    private Long id;\n    private String username;\n    private String email;\n    private String password;\n\n    public User() {}\n\n    public User(Long id, String username, String email, String password) {\n        this.id = id;\n        this.username = username;\n        this.email = email;\n        this.password = password;\n    }\n\n    public Long getId() {\n        return id;\n    }\n\n    public void setId(Long id) {\n        this.id = id;\n    }\n\n    public String getUsername() {\n        return username;\n    }\n\n    public void setUsername(String username) {\n        this.username = username;\n    }\n\n    public String getEmail() {\n        return email;\n    }\n\n    public void setEmail(String email) {\n        this.email = email;\n    }\n\n    public String getPassword() {\n        return password;\n    }\n\n    public void setPassword(String password) {\n        this.password = password;\n    }\n}\n'}]}, {'name': 'repository', 'folders': [], 'files': [{'name': 'UserRepository.java', 'content': 'package com.example.userservice.repository;\n\nimport com.example.userservice.model.User;\nimport org.springframework.data.jpa.repository.JpaRepository;\nimport org.springframework.stereotype.Repository;\n\n@Repository\npublic interface UserRepository extends JpaRepository<User, Long> {\n    User findByUsername(String username);\n}\n'}]}, {'name': 'service', 'folders': [], 'files': [{'name': 'UserService.java', 'content': 'package com.example.userservice.service;\n\nimport com.example.userservice.model.User;\nimport com.example.userservice.repository.UserRepository;\nimport org.springframework.beans.factory.annotation.Autowired;\nimport org.springframework.stereotype.Service;\nimport java.util.List;\nimport java.util.Optional;\n\n@Service\npublic class UserService {\n    @Autowired\n    private UserRepository userRepository;\n\n    public List<User> getAllUsers() {\n        return userRepository.findAll();\n    }\n\n    public User getUserById(Long id) {\n        Optional<User> user = userRepository.findById(id);\n        return user.orElse(null);\n    }\n\n    public User createUser(User user) {\n        return userRepository.save(user);\n    }\n\n    public User updateUser(Long id, User userDetails) {\n        Optional<User> optionalUser = userRepository.findById(id);\n        if (optionalUser.isPresent()) {\n            User user = optionalUser.get();\n            user.setUsername(userDetails.getUsername());\n            user.setEmail(userDetails.getEmail());\n            user.setPassword(userDetails.getPassword());\n            return userRepository.save(user);\n        } else {\n            return null;\n        }\n    }\n\n    public boolean deleteUser(Long id) {\n        if (userRepository.existsById(id)) {\n            userRepository.deleteById(id);\n            return true;\n        } else {\n            return false;\n        }\n    }\n}\n'}]}], 'files': [{'name': 'UserServiceApplication.java', 'content': 'package com.example.userservice;\n\nimport org.springframework.boot.SpringApplication;\nimport org.springframework.boot.autoconfigure.SpringBootApplication;\n\n@SpringBootApplication\npublic class UserServiceApplication {\n    public static void main(String[] args) {\n        SpringApplication.run(UserServiceApplication.class, args);\n    }\n}\n'}]}], 'files': []}], 'files': []}], 'files': []}, {'name': 'resources', 'folders': [], 'files': [{'name': 'application.properties', 'content': 'spring.datasource.url=jdbc:h2:mem:testdb\nspring.datasource.driverClassName=org.h2.Driver\nspring.datasource.username=sa\nspring.datasource.password=\nspring.jpa.database-platform=org.hibernate.dialect.H2Dialect\nspring.h2.console.enabled=true\nspring.jpa.hibernate.ddl-auto=update\nserver.port=8081\n'}]}], 'files': []}], 'files': []}], 'files': []}], 'files': [{'name': 'README.md', 'content': '# User Service\n\nThis is a Spring Boot microservice for managing users. It provides REST endpoints for CRUD operations on users.\n\n## How to Run\n\n1. Make sure you have Java 11+ and Maven installed.\n2. Navigate to the `user_service` directory.\n3. Run `mvn spring-boot:run`.\n\nThe service will start on port 8081.\n\n## API Endpoints\n\n- `GET /users` - List all users\n- `GET /users/{id}` - Get user by ID\n- `POST /users` - Create a new user\n- `PUT /users/{id}` - Update user\n- `DELETE /users/{id}` - Delete user\n'}, {'name': 'pom.xml', 'content': '<project xmlns="http://maven.apache.org/POM/4.0.0"\n         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">\n    <modelVersion>4.0.0</modelVersion>\n    <groupId>com.example</groupId>\n    <artifactId>user_service</artifactId>\n    <version>1.0.0</version>\n    <packaging>jar</packaging>\n    <name>User Service</name>\n    <description>Microservice for user management</description>\n    <parent>\n        <groupId>org.springframework.boot</groupId>\n        <artifactId>spring-boot-starter-parent</artifactId>\n        <version>2.7.5</version>\n        <relativePath/>\n    </parent>\n    <properties>\n        <java.version>11</java.version>\n    </properties>\n    <dependencies>\n        <dependency>\n            <groupId>org.springframework.boot</groupId>\n            <artifactId>spring-boot-starter-web</artifactId>\n        </dependency>\n        <dependency>\n            <groupId>org.springframework.boot</groupId>\n            <artifactId>spring-boot-starter-data-jpa</artifactId>\n        </dependency>\n        <dependency>\n            <groupId>com.h2database</groupId>\n            <artifactId>h2</artifactId>\n            <scope>runtime</scope>\n        </dependency>\n        <dependency>\n            <groupId>org.springframework.boot</groupId>\n            <artifactId>spring-boot-starter-test</artifactId>\n            <scope>test</scope>\n        </dependency>\n    </dependencies>\n    <build>\n        <plugins>\n            <plugin>\n                <groupId>org.springframework.boot</groupId>\n                <artifactId>spring-boot-maven-plugin</artifactId>\n            </plugin>\n        </plugins>\n    </build>\n</project>\n'}]}"""

if __name__ == "__main__":
    import string
    printable = string.ascii_letters + string.digits + string.punctuation + ' '
    def hex_escape(s):
        return ''.join(c if c in printable else r'\n' for c in s)
    print(hex_escape(single_quote_to_double_with_content(TEST)))


#!/usr/bin/env python3
"""
Parse a plain-text project document and create folders/files on disk.

Supports BOTH formats:
1) Simple:
     <relative/path/to/file>
     ----------------------------------------
     ```<language-optional>
     <full file content>
     ```

2) Titled header then sections (e.g.):
     User_Profile_Service_full_structure_and_code.txt
     ------------------------------------------------------------
     user-profile-service/pom.xml
     ----------------------------------------
     ```xml
     ... content ...
     ```
     user-profile-service/src/main/java/.../App.java
     ----------------------------------------
     ```java
     ... content ...
     ```

Usage:
  python text_to_fs.py --input project.txt --root ./out
  cat project.txt | python text_to_fs.py --root ./out
  python text_to_fs.py --input project.txt --root ./out --overwrite --verbose
  python text_to_fs.py --input project.txt --root ./out --dry-run

The dashed line may be any length >= 3 dashes. Language after ``` is optional.
"""
import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Iterable, Dict

DASHES_RE = re.compile(r"^\s*-{3,}\s*$")
FENCE_START_RE = re.compile(r"^\s*```([\w+-]*)\s*$")
FENCE_END_RE = re.compile(r"^\s*```\s*$")

class ParseError(Exception):
    pass

def normalize_rel_path(p: str) -> str:
    p = p.strip().replace("\\", "/")
    p = re.sub(r"^(?:\./|/)+", "", p)  # strip leading ./ or /
    p = re.sub(r"/+", "/", p)          # collapse ////
    if not p or p.endswith("/"):
        raise ValueError(f"Invalid file path: '{p}'")
    return p

def _is_path_header_line(line: str) -> bool:
    return bool(line and not FENCE_START_RE.match(line) and not FENCE_END_RE.match(line) and not DASHES_RE.match(line))

def _peek_next_nonempty_index(lines: List[str], start: int) -> int:
    j = start
    n = len(lines)
    while j < n and lines[j].strip() == "":
        j += 1
    return j

def parse_sections(text: str) -> List[Tuple[str, str]]:
    lines = text.splitlines()
    i, n = 0, len(lines)
    sections: List[Tuple[str, str]] = []

    while i < n:
        line = lines[i].rstrip("\n")

        # Look for a header-like line (candidate path) followed by dashes
        if not _is_path_header_line(line):
            i += 1
            continue

        j = _peek_next_nonempty_index(lines, i + 1)
        if j >= n or not DASHES_RE.match(lines[j]):
            # Not a section header; skip and continue
            i += 1
            continue

        # We have a candidate header (could be a decorative title or a real file path)
        header_line = line
        i = j + 1  # move past dashes

        k = _peek_next_nonempty_index(lines, i)
        if k < n and FENCE_START_RE.match(lines[k]):
            # It's a real file section: header + dashes + fenced code block
            try:
                rel_path = normalize_rel_path(header_line)
            except Exception:
                raise ParseError(f"Invalid file path header: '{header_line}'")

            # Parse fenced block
            i = k + 1  # skip fence start
            content_lines: List[str] = []
            while i < n and not FENCE_END_RE.match(lines[i]):
                content_lines.append(lines[i])
                i += 1
            if i >= n or not FENCE_END_RE.match(lines[i]):
                raise ParseError(f"Unterminated code fence for '{rel_path}' before EOF")
            i += 1  # consume closing fence

            content = "\n".join(content_lines)
            if content_lines and not content.endswith("\n"):
                content += "\n"
            sections.append((rel_path, content))
            continue

        # If the next non-empty line is ANOTHER header followed by dashes, then
        # treat the current header as a decorative title and continue scanning.
        if k < n and _is_path_header_line(lines[k]):
            j2 = _peek_next_nonempty_index(lines, k + 1)
            if j2 < n and DASHES_RE.match(lines[j2]):
                # Decorative title; continue from the next header candidate
                i = k
                continue

        # Otherwise, malformed section (expected a fence after dashes)
        raise ParseError(f"Expected code fence after dashes for '{header_line}' near line {i+1}")

    if not sections:
        raise ParseError("No file sections found. Ensure the document follows the required format.")
    return sections

def ensure_within_root(root: Path, dest: Path) -> None:
    # Prevent path traversal outside root
    root_abs = root.resolve()
    dest_abs = (root / dest).resolve()
    if os.path.commonpath([str(dest_abs), str(root_abs)]) != str(root_abs):
        raise ValueError(f"Refusing to write outside root: {dest_abs} not within {root_abs}")

def write_files(sections: List[Tuple[str, str]], root: Path, overwrite: bool = False, verbose: bool = False) -> list[Path]:
    created: list[Path] = []
    for rel, content in sections:
        dest = (root / rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        ensure_within_root(root, dest)
        if dest.exists() and not overwrite:
            raise FileExistsError(f"File exists: {dest}. Use --overwrite to replace.")
        if verbose:
            print(f"Writing {dest}")
        dest.write_text(content, encoding="utf-8")
        created.append(dest)
    return created

def build_tree(paths: Iterable[Path], root: Path) -> Dict[str, dict]:
    tree: Dict[str, dict] = {}
    root = root.resolve()
    for p in paths:
        rel = p.resolve().relative_to(root)
        node = tree
        parts = list(rel.parts)
        for d in parts[:-1]:
            node = node.setdefault(d, {})
        node[parts[-1]] = None
    return tree

def print_tree(tree: Dict[str, dict], prefix: str = "") -> None:
    items = list(tree.items())
    for idx, (name, val) in enumerate(items):
        is_last = idx == len(items) - 1
        branch = "└── " if is_last else "├── "
        print(prefix + branch + name)
        if isinstance(val, dict):
            print_tree(val, prefix + ("    " if is_last else "│   "))

def main(text, root):

    
    try:
        sections = parse_sections(text)
    except ParseError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    
    created = write_files(sections, root=root, overwrite=True, verbose=True)
    tree = build_tree(created, root=root)
    print(f"Created under: {root.resolve()}\n")
    print(str(root))
    print_tree(tree)


 # Concatenate document texts (truncate each to avoid blowing the context)
def _content(doc):
    # LlamaIndex docs often expose .get_content(); fall back to .text if needed
    try:
        return doc.get_content()
    except Exception:
        return getattr(doc, "text", "")