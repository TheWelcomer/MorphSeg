<script>
  import Bubbles from "./Bubbles.svelte"
  import Sparkles from "./Sparkles.svelte"

  const Stage = {
    BEFORE: 0,
    WORDS: 1,
    CLEANUP: 2,
    SWAPOUT: 3,
    ITS_MORPHEME_TIME: 4,
    DONE: 5,
  };

  let input = $state("What the Segma?");
  let stage = $state(Stage.BEFORE);
  let words = $state(splitWords(input));
  let morphemes = $state([["What"],["the"],["Seg","ma"]]);

  function splitWords(text) {
    return text.replace(/\s/g, " ")
               .split(" ")
               .filter((word)=>word.length > 0);
  }

  function segment(text) {
    return text.split(" ")
               .map((word)=>word.split(""))
               .filter((word)=>word.length > 0);
  }

  function delay(t) {
    return new Promise(resolve => {
      setTimeout(resolve, t);
    });
  }

  async function playAnimations() {
    stage = Stage.WORDS;
    await delay((words.length * 250) + 250);
    stage = Stage.CLEANUP;
    await delay(3500);
    stage = Stage.SWAPOUT;
    await delay(1500);
    stage = Stage.ITS_MORPHEME_TIME;
    await delay(2000);
    stage = Stage.DONE;
  }

  export function startAnimation() {
    words = splitWords(input);
    playAnimations();
  }

  export function stopAnimation() {
    stage = Stage.BEFORE;
  }
</script>

<div id=cutting-board>
  {#if stage == Stage.BEFORE}
    <div id=cutting-board-input bind:innerText={input} contenteditable=true />
  {:else if stage >= Stage.WORDS}
    <div id="word-container">
      {#if stage <= Stage.CLEANUP}
        {#each words as word, wIndex}
          <span class="word">
              <span class="word-inner word-style-{(wIndex % 5) + 1}">
                {word}
              </span>
          </span>&nbsp<span class="word-spacer" style="animation-delay: {wIndex * 0.25}s;"></span>
        {/each}
      {:else}
        {#each morphemes as word, wIndex}
          {#if stage >= Stage.ITS_MORPHEME_TIME}
            {#each word as morpheme, mIndex}
              <span class="word">
                  <span class="word-inner word-style-{(wIndex % 5) + 1}">
                    {morpheme}
                  </span>{#if mIndex != (word.length - 1)}
                    <span class="morpheme-spacer"></span>
                  {/if}
              </span>
            {/each}
          {:else}
            <span class="word">
              <span class="word-inner word-style-{(wIndex % 5) + 1}">
                {#each word as morpheme}
                  {morpheme}
                {/each}
              </span>
            </span>
          {/if}&nbsp<span class="canon-word-spacer"></span>
        {/each}
      {/if}
    </div>
  {/if}
  {#if stage >= Stage.CLEANUP && stage <= Stage.ITS_MORPHEME_TIME}
    <Bubbles />
  {:else if stage == Stage.DONE}
    <Sparkles />
  {/if}
</div>

{#if stage < Stage.ITS_MORPHEME_TIME}
  <img id="tomato" class="veggie" src="/assets/Sprite-Tomato.gif">
  <img id="carrot" class="veggie" src="/assets/Sprite-Carrot.gif">
  <img id="pepper" class="veggie" src="/assets/Sprite-Pepper.gif">
  <img id="broccoli" class="veggie" src="/assets/Sprite-Broccoli.gif">
  <img id="onion" class="veggie" src="/assets/Sprite-Onion.gif">
{:else}
  <img id="tomato" class="veggie" src="/assets/Sprite-Cut_Tomato.gif">
  <img id="carrot" class="veggie" src="/assets/Sprite-Cut_Carrot.gif">
  <img id="pepper" class="veggie" src="/assets/Sprite-Cut_Pepper.gif">
  <img id="broccoli" class="veggie" src="/assets/Sprite-Cut_Broccoli.gif">
  <img id="onion" class="veggie" src="/assets/Sprite-Cut_Onion.gif">
{/if}

<style>
  @import "./style.css";

  .veggie {
    width: 50vh;
    height: 50vh;
    position: absolute;
    z-index: 1;
  }

  #tomato {
    top: -10%;
    left: -6%;
  }

  #carrot {
    bottom: 0%;
    right: 0%;
  }

  #pepper {
    bottom: -7%;
    left: -7%;
  }

  #broccoli {
    bottom: -14%;
    right: 30%;
  }

  #onion {
    width: 35vh;
    height: 35vh;
    top: 0%;
    right: 0%;
  }
  
  #cutting-board {
    align-items: center;
    justify-content: center;
    display: flex;
    position: relative;
    background-image: url("/assets/Sprite-cuttingboard.png");
    background-repeat: no-repeat;
    background-size: contain;
    background-position: left center;
    margin: none;
  }

  #word-container {
    margin: 5% 18% 5% 5%;
    align-items: center;
    width: 100%;
  }

  .word {
    display: inline-block;
    margin: 0.25em 0 0.25em 0;
  }

  .word-inner {
    padding: 0.1em;
    border-radius: 0.3em;
    border-style: solid;
    border-width: 0.15em;
  }

  .word-style-1 {
    background-color: #b82634;
    border-color: #961743;
  }

  .word-style-2 {
    background-color: #d3802e;
    border-color: #c16a38;
  }

  .word-style-3 {
    background-color: #d0a94e;
    border-color: #d78d43;
  }

  .word-style-4 {
    background-color: #489d3e;
    border-color: #407b51;
  }

  .word-style-5 {
    background-color: #8a4896;
    border-color: #663479;
  }

  .word-spacer {
    animation: 0.5s ease-out 1 both expand;
    animation-iteration-count: 1;
    display: inline-block;
  }

  .morpheme-spacer {
    animation: 0.5s ease-out 0.2s 1 both expand-less;
    animation-iteration-count: 1;
    display: inline-block;
  }

  .canon-word-spacer {
    display: inline-block;
    width: 1em;
  }


  @keyframes expand {
    from {
      width: 0em;
    }
    to {
      width: 1.0em;
    }
  }

  @keyframes expand-less {
    from {
      width: 0em;
    }
    to {
      width: 0.5em;
    }
  }
</style>
