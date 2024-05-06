section .data:
    hello: "Hello world!", 0
    pointer: hello

section .text:

    .loop:
        load r0, (pointer)
        cmp r0, #0
        jz .end
        out r0, 1

        load r0, pointer
        inc r0
        store r0, pointer

        jmp .loop

    .end:
        halt