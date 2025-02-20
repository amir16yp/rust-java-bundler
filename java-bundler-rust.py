#!/usr/bin/env python3
import os
import shutil
import argparse
import zipfile
from pathlib import Path
from typing import List, Tuple

def find_java_path(jre_zip_path: str) -> tuple[str, str]:
    with zipfile.ZipFile(jre_zip_path) as zf:
        for path in zf.namelist():
            normalized = path.replace('\\', '/')
            if normalized.endswith('/bin/java') or normalized.endswith('/bin/java.exe'):
                parts = normalized.split('/')
                root_dir = parts[0]
                bin_index = parts.index('bin')
                return root_dir, '/'.join(parts[bin_index:])
    raise ValueError("Could not find java executable in JRE zip")

def create_cargo_toml(project_dir: Path, project_name: str) -> None:
    cargo_content = f'''[package]
name = "{project_name}"
version = "0.1.0"
edition = "2021"

[dependencies]
zip = "0.6"
'''
    with open(project_dir / "Cargo.toml", "w") as f:
        f.write(cargo_content)

def create_main_rs(project_dir: Path, additional_files: List[Tuple[str, str]], java_path: str, root_dir: str) -> None:
    additional_files_const = "\n".join(
        f'const {Path(file[0]).stem.upper()}_FILE: &[u8] = include_bytes!("{file[0]}");'
        for file in additional_files
    )
    
    files_vec = ",".join(
        f'("{file[0]}", {Path(file[0]).stem.upper()}_FILE)'
        for file in additional_files
    )

    main_content = f'''use std::fs::{{self, OpenOptions}};
use std::io::{{self, Write}};
use std::path::Path;
use std::process::Command;
use std::fs::create_dir_all;
use std::env;

const JRE_ZIP: &[u8] = include_bytes!("jre.zip");
const JAR_FILE: &[u8] = include_bytes!("app.jar");
{additional_files_const}

fn get_data_dir() -> io::Result<std::path::PathBuf> {{
    let current_dir = std::env::current_dir()?;
    Ok(current_dir)
}}

fn main() -> io::Result<()> {{
    let data_dir = get_data_dir()?;
    let jre_dir = data_dir.join("jre");
    
    if !jre_dir.exists() {{
        create_dir_all(&jre_dir)?;
        extract_zip(JRE_ZIP, &jre_dir)?;
    }}

    let jar_path = data_dir.join("app.jar");
    if !jar_path.exists() {{
        create_dir_all(&data_dir)?;
        write_file(&jar_path, JAR_FILE)?;
    }}

    let additional_files = vec![{files_vec}];
    bundle_additional_files(&data_dir, &additional_files)?;

    let java_exe = jre_dir.join("{java_path}");
    
    // Collect command line arguments
    let args: Vec<String> = env::args().skip(1).collect();
    
    // Build the command with all arguments
    let mut command = Command::new(java_exe);
    command.current_dir(&data_dir)  // Set working directory to where JAR is
           .arg("-jar")
           .arg(&jar_path);
    
    // Add any additional arguments
    if !args.is_empty() {{
        command.args(args);
    }}
    
    let status = command.status()?;

    if !status.success() {{
        return Err(io::Error::new(io::ErrorKind::Other, "Failed to launch JAR file"));
    }}

    Ok(())
}}

fn extract_zip(zip_data: &[u8], output_dir: &Path) -> io::Result<()> {{
    let mut archive = zip::ZipArchive::new(io::Cursor::new(zip_data))?;
    
    for i in 0..archive.len() {{
        let mut file = archive.by_index(i)?;
        let name = file.name().replace('\\\\', "/");
        
        // Skip the root directory itself
        if name == "{root_dir}/" {{
            continue;
        }}
        
        // Strip root directory from path
        let relative_path = name.strip_prefix("{root_dir}/")
            .unwrap_or(&name);

        let out_path = output_dir.join(relative_path);

        if name.ends_with('/') {{
            create_dir_all(&out_path)?;
        }} else {{
            if let Some(parent) = out_path.parent() {{
                create_dir_all(parent)?;
            }}
            let mut out_file = OpenOptions::new()
                .write(true)
                .create(true)
                .truncate(true)
                .open(&out_path)?;
            io::copy(&mut file, &mut out_file)?;
            
            // Make binaries executable on Unix-like systems
            #[cfg(unix)]
            if out_path.ends_with("java") || out_path.ends_with("java.exe") {{
                use std::os::unix::fs::PermissionsExt;
                let mut perms = out_file.metadata()?.permissions();
                perms.set_mode(0o755);
                std::fs::set_permissions(&out_path, perms)?;
            }}
        }}
    }}
    Ok(())
}}

fn write_file(path: &Path, data: &[u8]) -> io::Result<()> {{
    let mut file = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .open(path)?;
    file.write_all(data)?;
    Ok(())
}}

fn bundle_additional_files(base_dir: &Path, files: &[(&str, &[u8])]) -> io::Result<()> {{
    for (filename, data) in files {{
        let file_path = base_dir.join(filename);
        if !file_path.exists() {{
            write_file(&file_path, data)?;
        }}
    }}
    Ok(())
}}'''

    src_dir = project_dir / "src"
    src_dir.mkdir(exist_ok=True)
    with open(src_dir / "main.rs", "w") as f:
        f.write(main_content)

def create_rust_project(
    output_dir: str,
    project_name: str,
    jar_path: str,
    jre_path: str,
    additional_files: List[str]
) -> None:
    project_dir = Path(output_dir) / project_name
    src_dir = project_dir / "src"
    os.makedirs(src_dir, exist_ok=True)
    
    create_cargo_toml(project_dir, project_name)
    
    root_dir, java_path = find_java_path(jre_path)
    
    shutil.copy2(jar_path, src_dir / "app.jar")
    shutil.copy2(jre_path, src_dir / "jre.zip")
    
    additional_files_info = []
    for file_path in additional_files:
        dest_path = src_dir / Path(file_path).name
        shutil.copy2(file_path, dest_path)
        additional_files_info.append((Path(file_path).name, file_path))
    
    create_main_rs(project_dir, additional_files_info, java_path, root_dir)
    
    print(f"Created Rust project '{project_name}' in {project_dir}")
    print("\nTo build the project:")
    print(f"  cd {project_dir}")
    print("  cargo build --release")
    print("\nAfter building, you can run the application with arguments:")
    print(f"  ./target/release/{project_name} [args...]")

def main():
    parser = argparse.ArgumentParser(
        description="Generate a Rust project for bundling Java applications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  %(prog)s -o output_dir -n my-app -j app.jar -r jre.zip -f config.json assets/

After building, you can pass arguments to the Java application:
  ./my-app --config custom.properties
        """
    )
    parser.add_argument("--output", "-o", required=True, help="Output directory for the project")
    parser.add_argument("--name", "-n", required=True, help="Project name")
    parser.add_argument("--jar", "-j", required=True, help="Path to the JAR file")
    parser.add_argument("--jre", "-r", required=True, help="Path to the JRE zip file")
    parser.add_argument("--files", "-f", nargs="*", default=[], help="Additional files to bundle")
    
    args = parser.parse_args()
    
    create_rust_project(
        args.output,
        args.name,
        args.jar,
        args.jre,
        args.files
    )

if __name__ == "__main__":
    main()