# Script để cập nhật navigation trên tất cả các trang

$files = @(
    'app/templates/dashboard.html',
    'app/templates/sets_list.html',
    'app/templates/browse.html',
    'app/templates/upload.html',
    'app/templates/study.html',
    'app/templates/study_choice.html',
    'app/templates/study_fill.html',
    'app/templates/set_detail.html'
)

foreach ($file in $files) {
    Write-Host "Processing $file..."
    $content = Get-Content $file -Raw
    
    # Thay thế các nav button
    $content = $content -replace 'title="Feed">🏠</a>', 'title="Feed"><span class="icon">🏠</span> Feed</a>'
    $content = $content -replace 'title="Bộ từ của tôi">📚</a>', 'title="Bộ từ của tôi"><span class="icon">📚</span> Bộ từ</a>'
    $content = $content -replace 'title="Thống kê">📊</a>', 'title="Thống kê"><span class="icon">📊</span> Thống kê</a>'
    $content = $content -replace 'title="Tài khoản">(\s*<', 'title="Tài khoản"><$1'
    $content = $content -replace '(</\w+>\s*👤\s*</a>)', '</a>' # Remove standalone icon
    $content = $content -replace '(<a href="/profile"[^>]*title="Tài khoản"[^>]*>)', '$1<span class="icon">👤</span> Tài khoản'
    $content = $content -replace 'title="Đăng xuất">🚪</a>', 'title="Đăng xuất">Đăng xuất</a>'
    $content = $content -replace 'title="Quay lại bộ từ">↩️</a>', 'title="Quay lại bộ từ"><span class="icon">↩️</span> Quay lại</a>'
    $content = $content -replace 'title="Đổi chế độ">🔄</a>', 'title="Đổi chế độ"><span class="icon">🔄</span> Đổi chế độ</a>'
    
    # Update CSS
    $content = $content -replace '(\.nav-btn \{[^}]*font-size:\s*)[^;]+;', '$11em; font-weight: 600; display: flex; align-items: center; gap: 6px;'
    
    # Add icon style if not exists
    if ($content -notmatch '\.nav-btn \.icon') {
        $content = $content -replace '(\.nav-btn:hover \{)', '.nav-btn .icon { font-size: 1.3em; } $1'
    }
    
    Set-Content $file $content
}

Write-Host "Done!"
