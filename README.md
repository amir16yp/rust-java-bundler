# rust-java-bundler

A tool that generates standalone Rust executables that bundle Java applications with their own JRE. This eliminates the need for users to have Java installed on their system and simplifies distribution.

## Features

- Bundles a Java application (JAR) with a specific JRE
- Creates a single executable that includes everything needed to run
- Handles additional resource files and assets
- Supports passing command-line arguments to the Java application
- Cross-platform compatible (Windows, Linux, macOS)
- Zero Java installation required for end users

## Prerequisites

To use this generator, you need:

- Python 3.6 or later
- Rust toolchain (cargo, rustc)
- A Java application in JAR format
- A compatible JRE distribution in ZIP format

## Installation

1. Clone or download this repository
2. Ensure you have Python 3 and Rust installed
3. Make the script executable (Unix-like systems):
   ```bash
   chmod +x java-bundler-rust.py
   ```

## Usage

### Basic Usage

```bash
./java-bundler-rust.py -o <output_dir> -n <project_name> -j <jar_file> -r <jre_zip> [-f [files ...]]
```

### Arguments

- `-o, --output`: Output directory for the project
- `-n, --name`: Project name (will be used for the executable)
- `-j, --jar`: Path to your JAR file
- `-r, --jre`: Path to the JRE zip file
- `-f, --files`: Additional files to bundle (optional)

### Example

```bash
./java-bundler-rust.py -o dist -n my-app -j application.jar -r jre8.zip -f config.json assets/images/
```

### Building the Generated Project

After generating the project:

1. Navigate to the project directory:
   ```bash
   cd dist/my-app
   ```

2. Build the release version:
   ```bash
   cargo build --release
   ```

3. Find the executable in `target/release/`

### Running the Bundled Application

The generated executable can be run directly and supports passing arguments to the Java application:

```bash
./my-app [arguments]
```

Example with arguments:
```bash
./my-app --config custom.properties
```

## JRE Requirements

The JRE zip file should:
- Contain a complete Java Runtime Environment
- Include the `bin/java` or `bin/java.exe` executable
- Be compatible with your Java application
- Be appropriate for your target platform(s)

## Project Structure

The generated Rust project will have the following structure:

```
my-app/
├── Cargo.toml
└── src/
    ├── main.rs
    ├── app.jar
    ├── jre.zip
    └── [additional files...]
```

## Technical Details

The generator:
1. Creates a new Rust project
2. Embeds the JRE, JAR, and additional files as binary data
3. Implements extraction and execution logic
4. Handles platform-specific considerations (file permissions, paths)

The generated executable will:
1. Extract the JRE (if not already extracted)
2. Extract the JAR and additional files
3. Launch the Java application using the bundled JRE
4. Forward any command-line arguments to the Java application

## Limitations

- The final executable size will include the entire JRE and application
- Initial launch may take longer due to JRE extraction
- Platform-specific JREs must be used for cross-compilation

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for improvements and bug fixes.

## License

[Unlicense](https://raw.githubusercontent.com/amir16yp/rust-java-bundler/refs/heads/main/LICENSE)
