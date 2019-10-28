set tabstop=4       " The width of a TAB is set to 4.
" Still it is a \t. It is just that
" Vim will interpret it to be having
" a width of 4.
set shiftwidth=4    " Indents will have a width of 4
set softtabstop=4   " Sets the number of columns for a TAB
set expandtab       " Expand TABs to spaces
syntax on

call plug#begin()
Plug 'vim-airline/vim-airline'
Plug 'sjl/badwolf'
Plug 'roxma/nvim-completion-manager'
Plug 'hkupty/iron.nvim', { 'do': ':UpdateRemotePlugins' }
Plug 'hynek/vim-python-pep8-indent', {'for': ['python', 'python3']}
Plug 'zchee/deoplete-jedi', { 'for': 'python' }
Plug 'davidhalter/jedi-vim', { 'for': 'python' }
Plug 'neomake/neomake'
Plug 'tpope/vim-surround'
Plug 'tpope/vim-unimpaired'
Plug 'python/black'
Plug 'tpope/vim-commentary'
Plug 'fisadev/vim-isort'
Plug 'heavenshell/vim-pydocstring'
Plug 'haya14busa/incsearch.vim'
Plug 'yuttie/comfortable-motion.vim'
Plug 'scrooloose/nerdtree'
Plug 'mileszs/ack.vim'
Plug 'tpope/vim-sensible'
call plug#end()


" Some basics:
	nnoremap c "_c
	set nocompatible
	filetype plugin on
	syntax on
	set encoding=utf-8
	set number relativenumber
" Enable autocompletion:
	set wildmode=longest,list,full
" Disables automatic commenting on newline:
	autocmd FileType * setlocal formatoptions-=c formatoptions-=r formatoptions-=o

" Goyo plugin makes text more readable when writing prose:
	map <leader>f :Goyo \| set bg=light \| set linebreak<CR>

" Splits open at the bottom and right, which is non-retarded, unlike vim defaults.
	set splitbelow splitright


" python folding
let g:SimpylFold_docstring_preview = 1
let g:python_highlight_operators = 0
let g:python_highlight_space_errors = 0
let g:python_highlight_all = 1


" Run linter on write
autocmd! BufWritePost * Neomake

"let g:neomake_python_python_maker = neomake#makers#ft#python#python()
"let g:neomake_python_flake8_maker = neomake#makers#ft#python#flake8()
"let g:neomake_python_pylint_maker = {
"  \ 'args': [
"  \ '-d', 'W503,E203',
"  \ '-f', 'text',
"  \ '--msg-template="{path}:{line}:{column}:{C}: [{symbol}] {msg}"',
"  \ '-r', 'n'
"  \ ],
"  \ 'errorformat':
"  \ '%A%f:%l:%c:%t: %m,' .
"  \ '%A%f:%l: %m,' .
"  \ '%A%f:(%l): %m,' .
"  \ '%-Z%p^%.%#,' .
"  \ '%-G%.%#',
"  \ }
"let g:neomake_python_enabled_makers = ['pylint', 'python']
let g:neomake_python_enabled_makers = ['pyflakes']

" split navigations
nnoremap <C-J> <C-W>j
nnoremap <C-K> <C-W>k
nnoremap <C-L> <C-W>l
nnoremap <C-H> <C-W>h
nnoremap <C-N> :noh<CR>
nnoremap <C-W> :w<CR>
nnoremap <C-Q> :q<CR>
inoremap <C-J> <Esc><C-W>j
inoremap <C-K> <Esc><C-W>k
inoremap <C-L> <Esc><C-W>l
inoremap <C-H> <Esc><C-W>h
inoremap <C-Z> <Esc><C-Z>
inoremap <M-j> <Down>
inoremap <M-k> <Up>
inoremap <M-h> <Left>
inoremap <M-l> <Right>
inoremap <M-a> <CR>
inoremap JK <Esc>
tnoremap <C-J> <C-\><C-n><C-W>j
tnoremap <C-K> <C-\><C-n><C-W>k
tnoremap <C-L> <C-\><C-n><C-W>l
tnoremap <C-H> <C-\><C-n><C-W>h
tnoremap <C-Q> <C-\><C-n>:q<CR>
inoremap <C-Z> <C-\><C-n><C-Z>
tnoremap <Esc> <C-\><C-n>
inoremap JK <C-\><C-n>
tnoremap JK <C-\><C-n>
inoremap jk <C-\><C-n>
tnoremap jk <C-\><C-n>
tnoremap <C-D> <Nop>
nnoremap pdb o__import__("pdb").set_trace()<Esc>
inoremap pdb __import__("pdb").set_trace()
nnoremap ipdb oimport IPython; IPython.embed()<Esc>
inoremap ipdb import IPython; IPython.embed()
nnoremap imtis ofrom libronan.python.utils import tis, array2image, tensor2image, mask2image<Esc>
inoremap imtis from libronan.python.utils import tis, array2image, tensor2image, mask2image

vmap <C-Space> <Plug>(iron-send-motion)<Esc>
imap <C-Space> <Esc>0<S-v><Plug>(iron-send-motion)<Esc>
nmap <C-Space> 0<S-v><Plug>(iron-send-motion)<Esc>

nmap <silent> <M-j> <Plug>(pydocstring)

function! Vpy()
  let g:iron_repl_open_cmd = 'topleft vertical 100 split'
  IronRepl
endfunction
command Vpy call Vpy()

function! Hpy()
  let g:iron_repl_open_cmd = ''
  IronRepl
endfunction
command Hpy call Hpy()

function! Pdb()
  let g:iron_repl_open_cmd = ''
endfunction
command Pdb call Pdb()

autocmd BufWinEnter,WinEnter term://* startinsert

function! Print()
  :hardcopy > /tmp/vim_print.ps
  !ps2pdf /tmp/vim_print.ps
  !lp -d MFP_C-pro /tmp/vim_print.ps
endfunction

set hlsearch
hi Search ctermbg=LightBlue
hi Search ctermfg=Red

function! s:Template(file)
  execute ':0r /sequoia/data1/rriochet/.config/nvim/templates/' . a:file
endfunction
command! -nargs=1 Template call s:Template(<f-args>)

function! Ind2()
  set tabstop=2
  set shiftwidth=2
  set softtabstop=2
endfunction
command Ind2 call Ind2()

function! Ind4()
  set tabstop=4
  set shiftwidth=4
  set softtabstop=4
endfunction
command Ind4 call Ind4()

autocmd BufWritePre *.py execute ':Black'

command Mail e term:///sequoia/data1/rriochet/bin/mutt

if filereadable(expand("~/.vimrc_background"))
  let base16colorspace=256
  source ~/.vimrc_background
endif

let g:comfortable_motion_scroll_down_key = "j"
let g:comfortable_motion_scroll_up_key = "k"
nnoremap <silent> <C-d> :call comfortable_motion#flick(g:comfortable_motion_imp    ulse_multiplier * winheight(0) * 2)<CR>
nnoremap <silent> <C-u> :call comfortable_motion#flick(g:comfortable_motion_imp    ulse_multiplier * winheight(0) * -2)<CR>
nnoremap <silent> <C-f> :call comfortable_motion#flick(g:comfortable_motion_imp    ulse_multiplier * winheight(0) * 4)<CR>
nnoremap <silent> <C-b> :call comfortable_motion#flick(g:comfortable_motion_imp    ulse_multiplier * winheight(0) * -4)<CR>

nmap " :NERDTreeToggle<CR>

