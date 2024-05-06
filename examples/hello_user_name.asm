section .rodata:
    what: "What's your name?", 10, 0
    hello: "Hello, "
    buffer: resb 32
    pointer: what
    buf_pointer: buffer


section .text:
    di
    move r1, #1                 @ в r1 будут записываться символы со ввода
    move r3, #0                 @ в r3 лежит 0 для сравнения
    ei

    .loop:
        load r0, (pointer)      @ кладём в r0 символ
        cmp r0, r3              @ проверяем на нуль-терминатор
        jz .read_loop           @ если попался нуль-терминатор, то переходим к следующему шагу
        out r0, 1               @ иначе выводим символ
        load r0, pointer
        inc r0
        store r0, pointer       @ переключаем указатель на следующий символ
        jmp .loop

    .read_loop:
        di
        cmp r1, r3              @ проверяем на ноль регистр куда записывается ввод
        jz .loop2               @ если встретили нуль-терминатор, то ввод считан, можно переходить к выводу
        ei
        jmp .read_loop

    .loop2:
        load r4, hello
        store r4, pointer       @ обновляем указатель чтобы он смотрел на начало приветствия
    .ans_loop:
        load r0, (pointer)      @ загрузка символа
        cmp r0, r3              @ проверка на нуль-терминатор
        jz .end                 @ если дошли до нуль терминатора, то вывод окончен
        out r0, 1               @ иначе выводим символ

        load r0, pointer
        inc r0
        store r0, pointer       @ обновляем указатель

        jmp .loop

    .end:
        halt


.int1:
    in r1, 0
    store r1, (buf_pointer)
    load r2, buf_pointer
    inc r2
    store r2, buf_pointer
    iret