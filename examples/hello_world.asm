section .rodata:
    hello: "Hello world!", 0
    pointer: hello

section .text:
    move r3, #0

    .loop:
        load r0, (pointer)
        cmp r0, r3
        jz .end
        out r0, 1

        load r0, pointer
        inc r0
        store r0, pointer

        jmp .loop

    .end:
        halt