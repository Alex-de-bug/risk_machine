# Risc Machine. Эксперементальная модель процессора и транслятора

- Дениченко Александр Олегович, P3212
- asm | risc | neum | hw | tick -> instr | struct | trap -> stream | port | cstr | prob1 | cache
- Базовый вариант (без усложнения)

Примечания:
- Идеи для реализации модели процессора брались из документаций к MISP32, SPARC, ARM.


## Язык программирования
Синтаксис в расширенной БНФ.

```ebnf
<program> ::= { <section> }

<section> ::= "section" "." "text" ":" { <instruction> }
            | "section" "." "data" ":" { <data_definition> }
            | "int" <number> ":" { <interrupt_instruction> }

<instruction> ::= "ei"
               | "di"
               | "jmp" <label>
               | "jz" <label>
               | "jnz" <label>
               | "halt"
               | "move" <register> "," <operand>
               | "cmp" <register> "," <register>
               | "add" <register> "," <register> "," <register>
               | "sub" <register> "," <register> "," <register>
               | "mod" <register> "," <register> "," <register>
               | "load" <register> "," <address>
               | "store" <register> "," <address>
               | "in" <register> "," <number>
               | "out" <register> "," <number>
               | "inc" <register>
               | <label> ":"
               | <comment>

<interrupt_instruction> ::= "in" <register> "," <number>
                          | "out" <register> "," <number>
                          | "store" <register> "," <address>
                          | "load" <register> "," <address>
                          | "iret"
                          | <comment>

<data_definition> ::= <identifier> ":" <data_value>
                    | <comment>

<data_value> ::= <string>
               | <number>
               | "resb" <number>
               | <comment>

<address> ::= "(" <identifier> ")"
            | <identifier>

<register> ::= "r" <number>

<operand> ::= <register>
            | "#" <number>

<label> ::= "." <identifier>

<identifier> ::= <letter> { <letter> | <digit> }
              | <identifier> "." <identifier>

<number> ::= <digit> { <digit> }

<string> ::= "\"" { <character> } "\""

<letter> ::= "a" | "b" | "c" | ... | "z"
           | "A" | "B" | "C" | ... | "Z"

<digit> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

<character> ::= <any printable ASCII character except quotation mark>

<comment> ::= "@" { <any printable ASCII character> }
```

Команды:

todo

## Организация памяти

- Память соответствует фон Неймановской архитектуре.
- Размер машинного слова - 32 бита.
- Адресация - абсолютная.

```text
           memory
+----------------------------+
| 00 : jmp start address (k) |
| 01 : data (for example)    |
| 02 :      ...              | 
|           ...              | 
| k  : program start         |
|           ...              |
| n : interruption vector 1  |
+----------------------------+
```
- Ячейка памяти `0` соответствует инструкции jmp, которая осуществляет переход при цикле инициализации на адрес первой инструкции. 
- Ячейка памяти `n`, является последнем элементом памяти и соответствует `вектору прерывания 1`.
- Расположение кода и данных не 'прибито' и отдано на конечную реализацию программисту.
- Секция с данными обозначается `section .data:` (может отсутсвовать). В блоке данных могу быть:
  - `Целочисленные данные` -- под них отводится одна ячейка памяти;
  - `Строковые данные` -- под них отводится `n` последовательных ячеек памяти, где `n` - длина строки
      (`нуль-терминатор` оставлен на усмотрение программисту);
  - `Буферные данные` -- выделяются при помощи директивы `resb n`, где `n` - количество ячеек памяти, которое выделяется буфером при трансляции;
  - `Ссылочные` -- это `целочисленные` переменные, но при начальной инициализации хранят адрес другой переменной.
      Под них отводится одна ячейка памяти. 
- Переменные располагаются в памяти в таком порядке, в котором они прописаны в коде. Можно присваивать переменной строковые и целочисленные данные одновременно, перечисляя их через запятую.
- С ячейки памяти `k` начинаются инструкции, соответствующие исходному коду, прописанному в секции, которая обозначается как `.text`.


## Система команд

Особенности процессора:

- Машинное слово -- 32 бита, знаковое.
- Доступ к памяти осуществляется по адресу, хранящемуся в специальном регистре `PC (programm counter)`.
  Установка адреса осуществляется тремя разными способами:
    - Путем инкрементирования текущего значения, записанного в `PC`;
    - Путем записи значения из `ALU`;
    - Путем записи адреса из `Interruption Controller`.
- Поток управления:
    - увеличение `PC` на `1` после каждой команды (увеличение зависит от выполненной команды;)
    - условный (`jz` или `jnz`) и безусловный (`jmp`) переходы
    - прерывания, при которых в `PC` происходит запись адреса вектора из `Interruption Controller`, причём `PC` заранее сохарняется в `R12`. 

### Набор инструкций

Команды языка однозначно транслируюстя в инструкции


| Инструкция | Кол-во тактов |
|:-----------|---------------|
| nop        | 0             |
| add        | 4             |
| sub        | 4             |
| mul        | 4             |
| div        | 4             |
| mod        | 4             |
| inc        | 3             |
| dec        | 3             |
| dup        | 3             |
| over       | 5             |
| switch     | 4             |
| cmp        | 4             |
| jmp        | 2             |
| jz         | 1 или 2       |
| jnz        | 1 или 2       |
| call       | 4             |
| ret        | 2             |
| lit        | 2             |
| push       | 4             |
| pop        | 5             |
| drop       | 1             |
| ei         | 1             |
| di         | 1             |
| iret       | 0 или 2       |

Стоит учитывать, что в таблице приведено кол-во тактов на `цикл исполнения` инструкции.
`Цикл выборки` следующей инструкции выполняется за `2` такта.