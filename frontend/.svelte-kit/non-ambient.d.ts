
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	export interface AppTypes {
		RouteId(): "/" | "/showcase";
		RouteParams(): {
			
		};
		LayoutParams(): {
			"/": Record<string, never>;
			"/showcase": Record<string, never>
		};
		Pathname(): "/" | "/showcase" | "/showcase/";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): "/assets/Sprite-Alexis_Chef.gif" | "/assets/Sprite-Broccoli.gif" | "/assets/Sprite-Bubble.gif" | "/assets/Sprite-Bubble2.gif" | "/assets/Sprite-Bubble3.gif" | "/assets/Sprite-Carrot.gif" | "/assets/Sprite-Cut.gif" | "/assets/Sprite-Cut_Broccoli.gif" | "/assets/Sprite-Cut_Carrot.gif" | "/assets/Sprite-Cut_Onion.gif" | "/assets/Sprite-Cut_Pepper.gif" | "/assets/Sprite-Cut_Tomato.gif" | "/assets/Sprite-Cynthia_Chef.gif" | "/assets/Sprite-Donny_Chef.gif" | "/assets/Sprite-Knife_Cursor.aseprite" | "/assets/Sprite-Knife_Cursor.gif" | "/assets/Sprite-Knife_Cursorv2.aseprite" | "/assets/Sprite-Knife_Cursorv2.png" | "/assets/Sprite-Nathan_Chef.gif" | "/assets/Sprite-Onion.gif" | "/assets/Sprite-Pepper.gif" | "/assets/Sprite-Sparkle Hut!.gif" | "/assets/Sprite-Sparkle.gif" | "/assets/Sprite-Sponge.gif" | "/assets/Sprite-Taoran_Chef.gif" | "/assets/Sprite-Tomato.gif" | "/assets/Sprite-cuttingboard.png" | "/assets/nokia_cellphone/nokiafc22.ttf" | "/assets/nokia_cellphone/nokiafc22.txt" | "/robots.txt" | string & {};
	}
}