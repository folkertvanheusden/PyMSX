#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <z80ex/z80ex.h>
#include <z80ex/z80ex_dasm.h>

uint8_t ram[16384];

Z80EX_BYTE read_mem_cb(Z80EX_CONTEXT *z80, Z80EX_WORD addr, int m1_state, void *user_data)
{
	return ram[addr];
}

void write_mem_cb(Z80EX_CONTEXT *z80, Z80EX_WORD addr, Z80EX_BYTE value, void *user_data)
{
	ram[addr] = value;
}

void write_port(Z80EX_CONTEXT *z80, Z80EX_WORD port, Z80EX_BYTE value, void *user_data)
{
}

Z80EX_BYTE read_port(Z80EX_CONTEXT *z80, Z80EX_WORD port, void *user_data)
{
	return 0;
}

Z80EX_BYTE read_interrupt_vector(Z80EX_CONTEXT *z80, void *user_data)
{
	return 0;
}

Z80EX_CONTEXT * init_test()
{
	memset(ram, 0x00, sizeof ram);

	Z80EX_CONTEXT *z80 = z80ex_create(read_mem_cb, NULL, write_mem_cb, NULL, read_port, NULL, write_port, NULL, read_interrupt_vector, NULL);

	z80ex_set_reg(z80, regAF, 0x0000);
	z80ex_set_reg(z80, regPC, 0x0000);
	z80ex_set_reg(z80, regSP, 0x3fff);

	return z80;
}

void uninit_test(Z80EX_CONTEXT *const z80)
{
	z80ex_destroy(z80);
}

void dump_state(const char *const name, Z80EX_CONTEXT *const z80, int endaddr, int cycles)
{
	printf("%s ", name);

	for(int i=0; i<endaddr; i++)
		printf("%02x ", ram[i]);

	printf("| %04x %d", endaddr, cycles);

	for(int i=regAF; i<=regIFF2; i++)
		printf(" %04x", z80ex_get_reg(z80, Z80_REG_T(i)));

	printf("\n");
}

void memcheck(int a, uint8_t v)
{
	assert(ram[a] == v); // sanity check

	printf("memchk %04x %02x\n", a, v);
}

void run(Z80EX_CONTEXT *const z80, int endaddr)
{
	int cycles = 0;

	do {
		cycles += z80ex_step(z80);
	}
	while(z80ex_get_reg(z80, regPC) < endaddr || (endaddr == 0 && z80ex_last_op_type(z80) != 0));

	dump_state("after", z80, endaddr, cycles);
}

uint8_t get(Z80EX_CONTEXT *const z80, const int reg_nr)
{
	if (reg_nr == 0)
		return z80ex_get_reg(z80, regBC) >> 8;
	else if (reg_nr == 1)
		return z80ex_get_reg(z80, regBC) & 255;
	else if (reg_nr == 2)
		return z80ex_get_reg(z80, regDE) >> 8;
	else if (reg_nr == 3)
		return z80ex_get_reg(z80, regDE) & 255;
	else if (reg_nr == 4)
		return z80ex_get_reg(z80, regHL) >> 8;
	else if (reg_nr == 5)
		return z80ex_get_reg(z80, regHL) & 255;
	else if (reg_nr == 6)
		return ram[z80ex_get_reg(z80, regHL)];
	else if (reg_nr == 7)
		return z80ex_get_reg(z80, regAF) >> 8;
	
	assert(0);
}

void set(Z80EX_CONTEXT *const z80, const int reg_nr, const uint8_t vin)
{
	if (reg_nr == 0)
		z80ex_set_reg(z80, regBC, (z80ex_get_reg(z80, regBC) & 0x00ff) | (vin << 8));
	else if (reg_nr == 1)
		z80ex_set_reg(z80, regBC, (z80ex_get_reg(z80, regBC) & 0xff00) | vin);
	else if (reg_nr == 2)
		z80ex_set_reg(z80, regDE, (z80ex_get_reg(z80, regDE) & 0x00ff) | (vin << 8));
	else if (reg_nr == 3)
		z80ex_set_reg(z80, regDE, (z80ex_get_reg(z80, regDE) & 0xff00) | vin);
	else if (reg_nr == 4)
		z80ex_set_reg(z80, regHL, (z80ex_get_reg(z80, regHL) & 0x00ff) | (vin << 8));
	else if (reg_nr == 5)
		z80ex_set_reg(z80, regHL, (z80ex_get_reg(z80, regHL) & 0xff00) | vin);
	else if (reg_nr == 6)
		ram[z80ex_get_reg(z80, regHL)] = vin;
	else if (reg_nr == 7)
		z80ex_set_reg(z80, regAF, (z80ex_get_reg(z80, regAF) & 0x00ff) | (vin << 8));
	else
		assert(0);
}

void emit_rlc()
{
	for(int f=0; f<256; f++) {
		for(int instr=0x00; instr<0x08; instr++) {
			for(int v=0; v<256; v++) {
				Z80EX_CONTEXT *z80 = init_test();

				z80ex_set_reg(z80, regAF, f);
				set(z80, instr & 0x07, v);
				ram[0] = 0xcb;
				ram[1] = instr;
				ram[2] = 99;
				z80ex_set_reg(z80, regHL, 2);

				dump_state("before", z80, 0x0003, 0);

				run(z80, 0x0002);

				uninit_test(z80);
			}
		}
	}
}

void emit_rrc()
{
	for(int f=0; f<256; f++) {
		for(int instr=0x08; instr<0x10; instr++) {
			for(int v=0; v<256; v++) {
				Z80EX_CONTEXT *z80 = init_test();

				z80ex_set_reg(z80, regAF, f);
				set(z80, instr & 0x07, v);
				ram[0] = 0xcb;
				ram[1] = instr;
				ram[2] = 99;
				z80ex_set_reg(z80, regHL, 2);

				dump_state("before", z80, 0x0003, 0);

				run(z80, 0x0002);

				uninit_test(z80);
			}
		}
	}
}

void emit_rl()
{
	for(int f=0; f<256; f++) {
		for(int instr=0x10; instr<0x18; instr++) {
			for(int v=0; v<256; v++) {
				Z80EX_CONTEXT *z80 = init_test();

				z80ex_set_reg(z80, regAF, f);
				set(z80, instr & 0x07, v);
				ram[0] = 0xcb;
				ram[1] = instr;
				ram[2] = 99;
				z80ex_set_reg(z80, regHL, 2);

				dump_state("before", z80, 0x0003, 0);

				run(z80, 0x0002);

				uninit_test(z80);
			}
		}
	}
}

void emit_rr()
{
	for(int f=0; f<256; f++) {
		for(int instr=0x18; instr<0x20; instr++) {
			for(int v=0; v<256; v++) {
				Z80EX_CONTEXT *z80 = init_test();

				z80ex_set_reg(z80, regAF, f);
				set(z80, instr & 0x07, v);
				ram[0] = 0xcb;
				ram[1] = instr;
				ram[2] = 99;
				z80ex_set_reg(z80, regHL, 2);

				dump_state("before", z80, 0x0003, 0);

				run(z80, 0x0002);

				uninit_test(z80);
			}
		}
	}
}

void emit_sla()
{
	for(int instr=0x20; instr<0x28; instr++) {
		for(int v=0; v<256; v++) {
			Z80EX_CONTEXT *z80 = init_test();

			set(z80, instr & 0x07, v);
			ram[0] = 0xcb;
			ram[1] = instr;
			ram[2] = 99;
			z80ex_set_reg(z80, regHL, 2);

			dump_state("before", z80, 0x0003, 0);

			run(z80, 0x0002);

			uninit_test(z80);
		}
	}
}

void emit_sra()
{
	for(int f=0; f<256; f++) {
		for(int instr=0x28; instr<0x30; instr++) {
			for(int v=0; v<256; v++) {
				Z80EX_CONTEXT *z80 = init_test();

				z80ex_set_reg(z80, regAF, f);
				set(z80, instr & 0x07, v);
				ram[0] = 0xcb;
				ram[1] = instr;
				ram[2] = 99;
				z80ex_set_reg(z80, regHL, 2);

				dump_state("before", z80, 0x0003, 0);

				run(z80, 0x0002);

				uninit_test(z80);
			}
		}
	}
}

void emit_sll()
{
	for(int instr=0x30; instr<0x38; instr++) {
		for(int v=0; v<256; v++) {
			Z80EX_CONTEXT *z80 = init_test();

			set(z80, instr & 0x07, v);
			ram[0] = 0xcb;
			ram[1] = instr;
			ram[2] = 99;
			z80ex_set_reg(z80, regHL, 2);

			dump_state("before", z80, 0x0003, 0);

			run(z80, 0x0002);

			uninit_test(z80);
		}
	}
}

void emit_srl()
{
	for(int instr=0x38; instr<0x40; instr++) {
		for(int v=0; v<256; v++) {
			Z80EX_CONTEXT *z80 = init_test();

			set(z80, instr & 0x07, v);
			ram[0] = 0xcb;
			ram[1] = instr;
			ram[2] = 99;
			z80ex_set_reg(z80, regHL, 2);

			dump_state("before", z80, 0x0003, 0);

			run(z80, 0x0002);

			uninit_test(z80);
		}
	}
}

void emit_daa()
{
	for(int f=0; f<256; f++) {
		for(int v=0; v<256; v++) {
			Z80EX_CONTEXT *z80 = init_test();

			z80ex_set_reg(z80, regAF, f);
			set(z80, 0x07, v);
			ram[0] = 0x27;

			dump_state("before", z80, 0x0001, 0);

			run(z80, 0x0001);

			uninit_test(z80);
		}
	}
}

void emit_cpl()
{
	for(int v=0; v<256; v++) {
		Z80EX_CONTEXT *z80 = init_test();

		set(z80, 0x07, v);
		ram[0] = 0x2f;

		dump_state("before", z80, 0x0001, 0);

		run(z80, 0x0001);

		uninit_test(z80);
	}
}

void emit_scf()
{
	for(int v=0; v<256; v++) {
		Z80EX_CONTEXT *z80 = init_test();

		set(z80, 0x07, v);
		ram[0] = 0x37;

		dump_state("before", z80, 0x0001, 0);

		run(z80, 0x0001);

		uninit_test(z80);
	}
}

void emit_ccf()
{
	for(int f=0; f<256; f++) {
		for(int v=0; v<256; v++) {
			Z80EX_CONTEXT *z80 = init_test();

			z80ex_set_reg(z80, regAF, f);
			set(z80, 0x07, v);
			ram[0] = 0x3f;

			dump_state("before", z80, 0x0001, 0);

			run(z80, 0x0001);

			uninit_test(z80);
		}
	}
}

void emit_ld_ixy(uint8_t which)
{
	// mirror
	for(int instr=0x40; instr<0x60; instr++) {
		int t = instr & 7;
		if (t == 4 || t == 5 || t == 6)
			continue;

		int regfrom = t;
		int regto = (instr / 0x08) - 8;

		for(int v=0; v<256; v++) {
			Z80EX_CONTEXT *z80 = init_test();

			set(z80, regfrom, v);
			set(z80, regto, v ^ 0xff);

			ram[0] = which;
			ram[1] = instr;

			dump_state("before", z80, 0x0002, 0);

			run(z80, 0x0002);

			uninit_test(z80);
		}
	}

	// LD IXY[lh], r
	for(int instr=0x60; instr<0x70; instr++) {
		for(int v=0; v<256; v++) {
			Z80EX_CONTEXT *z80 = init_test();

			set(z80, instr & 7, v);
			ram[0] = which;
			ram[1] = instr;
			ram[2] = 1;
			ram[3] = 0x81;

			z80ex_set_reg(z80, which == 0xdd ? regIX : regIY, 0x1234);

			dump_state("before", z80, 0x0004, 0);

			run(z80, 0x0002);

			uninit_test(z80);
		}
	}

	// ld r,ixh	ld r,ixl	ld r,(ix+*)
	for(int instr=0x40; instr<0x80; instr++) {
		if ((instr & 0xf8) == 0x70)
			continue;
		int t = instr & 7;
		if (t != 4 && t != 5 && t != 6)
			continue;

		int reg = (instr / 0x08) - 8;

		for(int o=-128; o<128; o++) {
			for(int v=0; v<256; v++) {
				Z80EX_CONTEXT *z80 = init_test();

				set(z80, reg, v);
				ram[0] = which;
				ram[1] = instr;

				if (reg == 6) {
					ram[2] = o & 0xff;
					ram[0x2000 + o] = v;
					z80ex_set_reg(z80, which == 0xdd ? regIX : regIY, 0x2000);
				}
				else {
					z80ex_set_reg(z80, which == 0xdd ? regIX : regIY, (v ^ 0xff) | (v << 8));
				}

				dump_state("before", z80, reg == 6 ? 0x0003 : 0x0002, 0);

				run(z80, reg == 6 ? 0x0003 : 0x0002);

				uninit_test(z80);
			}
		}
	}

	// LD (IXY+*),r
	for(int instr=0x70; instr<0x78; instr++) {
		if (instr == 0x76)
			continue;

		for(int o=-128; o<128; o++) {
			for(int v=0; v<256; v++) {
				Z80EX_CONTEXT *z80 = init_test();

				set(z80, instr & 7, v);
				ram[0] = which;
				ram[1] = instr;
				ram[2] = o & 0xff;

				z80ex_set_reg(z80, which == 0xdd ? regIX : regIY, 0x2000);

				dump_state("before", z80, 0x0003, 0);

				run(z80, 0x0003);

				memcheck(0x2000 + o, v);

				uninit_test(z80);
			}
		}
	}
}

void emit_ld_ixy_misc(uint8_t which)
{
	// LD IX/Y,****
	{
		Z80EX_CONTEXT *z80 = init_test();

		ram[0] = which;
		ram[1] = 0x21;
		ram[2] = 1;
		ram[3] = 0x81;
		z80ex_set_reg(z80,  which == 0xdd ? regIX : regIY, 0x1234);

		dump_state("before", z80, 0x0004, 0);

		run(z80, 0x0004);

		uninit_test(z80);
	}
	 
	// ld (**),ix
	{
		Z80EX_CONTEXT *z80 = init_test();

		ram[0] = which;
		ram[1] = 0x22;
		ram[2] = 0x34;
		ram[3] = 0x12;
		z80ex_set_reg(z80,  which == 0xdd ? regIX : regIY, 0x2233);

		dump_state("before", z80, 0x0004, 0);

		run(z80, 0x0004);

		memcheck(0x1234, 0x33);
		memcheck(0x1235, 0x22);

		uninit_test(z80);
	}

	// ld ixh,*
	{
		Z80EX_CONTEXT *z80 = init_test();

		ram[0] = which;
		ram[1] = 0x26;
		ram[2] = 0x04;

		dump_state("before", z80, 0x0003, 0);

		run(z80, 0x0003);

		uninit_test(z80);
	}

	// ld ixl,*
	{
		Z80EX_CONTEXT *z80 = init_test();

		ram[0] = which;
		ram[1] = 0x2e;
		ram[2] = 0x04;

		dump_state("before", z80, 0x0003, 0);

		run(z80, 0x0003);

		uninit_test(z80);
	}

	// ld ix,(**)
	{
		Z80EX_CONTEXT *z80 = init_test();

		ram[0] = which;
		ram[1] = 0x2a;
		ram[2] = 0x04;
		ram[3] = 0x00;
		ram[4] = 0x33;
		ram[5] = 0x22;

		dump_state("before", z80, 0x0006, 0);

		run(z80, 0x0004);

		uninit_test(z80);
	}

	// ld (ix+*),*
	{
		Z80EX_CONTEXT *z80 = init_test();

		ram[0] = which;
		ram[1] = 0x36;
		ram[2] = 0x01;
		ram[3] = 0x12;
		z80ex_set_reg(z80,  which == 0xdd ? regIX : regIY, 0x2233);

		dump_state("before", z80, 0x0006, 0);

		run(z80, 0x0004);

		memcheck(0x2234, 0x12);

		uninit_test(z80);
	}

	// ld sp,ix
	{
		Z80EX_CONTEXT *z80 = init_test();

		ram[0] = which;
		ram[1] = 0xf9;
		z80ex_set_reg(z80,  which == 0xdd ? regIX : regIY, 0x1234);

		dump_state("before", z80, 0x0006, 0);

		run(z80, 0x0004);

		uninit_test(z80);
	}
}

void emit_aluop_a_nn()
{
	for(int instr=0xc6; instr<0x106; instr += 0x08) {
		for(int f=0; f<256; f++) {
			for(int v1=0; v1<256; v1++) {
				for(int v2=0; v2<256; v2++) {
					Z80EX_CONTEXT *z80 = init_test();

					z80ex_set_reg(z80, regAF, f);
					set(z80, 0x07, v1);
					ram[0] = instr;
					ram[1] = v2;

					dump_state("before", z80, 0x0002, 0);

					run(z80, 0x0002);

					uninit_test(z80);
				}
			}
		}
	}
}

void emit_dec_inc()
{
	// DEC B
	for(int f=0; f<256; f++) {
		for(int v=0; v<256; v++) {
			Z80EX_CONTEXT *z80 = init_test();

			z80ex_set_reg(z80, regAF, f);
			set(z80, 0x00, v); // set B
			ram[0] = 0x05;

			dump_state("before", z80, 0x0001, 0);

			run(z80, 0x0001);

			uninit_test(z80);
		}
	}

	// INC B
	for(int f=0; f<256; f++) {
		for(int v=0; v<256; v++) {
			Z80EX_CONTEXT *z80 = init_test();

			z80ex_set_reg(z80, regAF, f);
			set(z80, 0x00, v); // set B
			ram[0] = 0x04;

			dump_state("before", z80, 0x0001, 0);

			run(z80, 0x0001);

			uninit_test(z80);
		}
	}
}

void emit_bit()
{
	for(int instr=0x40; instr<0x80; instr++) {
		for(int f=0; f<256; f++) {
			for(int v=0; v<256; v++) {
				Z80EX_CONTEXT *z80 = init_test();

				z80ex_set_reg(z80, regAF, f);
				z80ex_set_reg(z80, regHL, 0x0002);
				set(z80, instr & 7, v);
				ram[0] = 0xcb;
				ram[1] = instr;
				ram[2] = v;

				dump_state("before", z80, 0x0002, 0);

				run(z80, 0x0002);

				uninit_test(z80);
			}
		}
	}
}

void emit_adc_pair()
{
	for(int v1=0; v1<65536; v1++) {
		for(int v2=0; v2<65536; v2++) {
			for(int instr=0x4a; instr<0x80; instr += 16) {
				for(int f=0; f<256; f++) {
					Z80EX_CONTEXT *z80 = init_test();

					z80ex_set_reg(z80, regHL, v1);

					if (instr == 0x4a)
						z80ex_set_reg(z80, regBC, v2);
					else if (instr == 0x5a)
						z80ex_set_reg(z80, regDE, v2);
					else if (instr == 0x6a)
						z80ex_set_reg(z80, regHL, v2);
					else if (instr == 0x7a)
						z80ex_set_reg(z80, regSP, v2);

					ram[0] = 0xed;
					ram[1] = instr;

					dump_state("before", z80, 0x0002, 0);

					run(z80, 0x0002);

					uninit_test(z80);
				}
			}
		}
	}
}

void emit_sbc_pair()
{
	for(int v1=0; v1<65536; v1++) {
		for(int v2=0; v2<65536; v2++) {
			for(int instr=0x42; instr<0x80; instr += 16) {
				for(int f=0; f<256; f++) {
					Z80EX_CONTEXT *z80 = init_test();

					z80ex_set_reg(z80, regHL, v1);

					if (instr == 0x4a)
						z80ex_set_reg(z80, regBC, v2);
					else if (instr == 0x5a)
						z80ex_set_reg(z80, regDE, v2);
					else if (instr == 0x6a)
						z80ex_set_reg(z80, regHL, v2);
					else if (instr == 0x7a)
						z80ex_set_reg(z80, regSP, v2);

					ram[0] = 0xed;
					ram[1] = instr;

					dump_state("before", z80, 0x0002, 0);

					run(z80, 0x0002);

					uninit_test(z80);
				}
			}
		}
	}
}

int main(int arg, char *argv[])
{
#if 0
	emit_rlc();
	emit_rrc();
	emit_rl();
	emit_rr();
	emit_sla();
	emit_sra();
	emit_sll();
	emit_srl();
	emit_daa();
	emit_cpl();
	emit_scf();
	emit_ccf();
	emit_ld_ixy(0xdd);
	emit_ld_ixy(0xfd);
	emit_ld_ixy_misc(0xdd);
	emit_ld_ixy_misc(0xfd);
	emit_aluop_a_nn();
	emit_dec_inc();
	emit_bit();
	emit_adc_pair();
#endif
	emit_sbc_pair();

	return 0;
}
