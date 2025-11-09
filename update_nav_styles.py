import re
import os

files = [
    'app/templates/feed.html',
    'app/templates/dashboard.html',
    'app/templates/browse.html',
    'app/templates/upload.html',
    'app/templates/study.html',
    'app/templates/study_choice.html',
    'app/templates/study_fill.html',
    'app/templates/set_detail.html',
]

for file_path in files:
    if not os.path.exists(file_path):
        print(f"❌ Skip {file_path} - not found")
        continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Update .nav-btn font-size to 1.1em
    content = re.sub(
        r'(\.nav-btn\s*\{[^}]*?font-size:\s*)[\d.]+em',
        r'\g<1>1.1em',
        content,
        flags=re.DOTALL
    )
    
    # Add font-weight: 700 if not exists
    if '.nav-btn' in content and 'font-weight: 700' not in content:
        content = re.sub(
            r'(\.nav-btn\s*\{[^}]*?)(color:)',
            r'\g<1>font-weight: 700;\n      \g<2>',
            content,
            flags=re.DOTALL
        )
    
    # Add display: flex and align-items if not exists
    if '.nav-btn' in content and 'display: flex' not in content:
        content = re.sub(
            r'(\.nav-btn\s*\{[^}]*?)(transition:)',
            r'\g<1>display: flex;\n      align-items: center;\n      gap: 8px;\n      \g<2>',
            content,
            flags=re.DOTALL
        )
    
    # Add SVG icon styles if not exists
    if '.nav-btn' in content and 'svg.icon' not in content:
        content = re.sub(
            r'(\.nav-btn:hover\s*\{[^}]*?\})',
            r'\g<1>\n\n    .nav-btn svg.icon {\n      width: 22px;\n      height: 22px;\n      flex-shrink: 0;\n      vertical-align: middle;\n    }',
            content,
            flags=re.DOTALL
        )
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated {file_path}")
    else:
        print(f"⚠️  No changes needed in {file_path}")

print("\n✅ Done updating all nav styles!")
