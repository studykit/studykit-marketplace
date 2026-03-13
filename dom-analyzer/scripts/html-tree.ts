#!/usr/bin/env -S deno run --allow-read

import { JSDOM, VirtualConsole } from 'npm:jsdom@28.1.0';
import fs from 'node:fs';
import path from 'node:path';

interface VisualizerOptions {
  showTextNodes?: boolean;
  maxDepth?: number;
  showAttributes?: boolean;
  compact?: boolean;
  outputFile?: string;
  selector?: string;
  showParents?: number;
  highlightPath?: boolean;
  matchIndex?: number;
}


class DOMHierarchyVisualizer {
  private output: string[] = [];
  private options: VisualizerOptions;

  constructor(options: VisualizerOptions = {}) {
    this.options = {
      showTextNodes: false,
      maxDepth: Infinity,
      showAttributes: true,
      compact: true,
      ...options
    };
  }

  public visualize(htmlContent: string): string {
    const virtualConsole = new VirtualConsole();
    virtualConsole.on('error', () => {}); // Suppress JSDOM errors

    const dom = new JSDOM(htmlContent, { virtualConsole });
    const document = dom.window.document;

    this.output = [];

    if (this.options.selector) {
      return this.visualizeFromNodes(document);
    }

    this.output.push('DOM Hierarchy Visualization');
    this.output.push('─'.repeat(50));

    this.traverseNode(document.documentElement, 0);

    return this.output.join('\n');
  }

  private visualizeFromNodes(document: Document): string {
    const nodes = this.findNodesBySelector(document, this.options.selector!);

    this.output.push('DOM Hierarchy Visualization');
    this.output.push('─'.repeat(50));
    this.output.push(`Selector: "${this.options.selector}"`);
    this.output.push(`Found: ${nodes.length} match${nodes.length !== 1 ? 'es' : ''}`);

    if (nodes.length === 0) {
      this.output.push('');
      this.output.push(`No elements found matching selector: "${this.options.selector}"`);
      return this.output.join('\n');
    }

    const nodesToShow = this.options.matchIndex
      ? [nodes[this.options.matchIndex - 1]].filter(Boolean)
      : nodes;

    if (this.options.matchIndex && !nodes[this.options.matchIndex - 1]) {
      this.output.push('');
      this.output.push(`Invalid match index: ${this.options.matchIndex}. Valid range: 1-${nodes.length}`);
      return this.output.join('\n');
    }

    nodesToShow.forEach((node, index) => {
      const actualIndex = this.options.matchIndex ? this.options.matchIndex - 1 : index;
      this.output.push('');
      this.output.push(`=== Match ${actualIndex + 1} of ${nodes.length} ===`);

      const path = this.getNodePathWithIndices(node);
      this.output.push(`Path: ${path}`);

      if (this.options.highlightPath) {
        this.output.push('>>> SELECTED NODE <<<');
      }

      if (this.options.showParents && this.options.showParents > 0) {
        this.visualizeWithContext(node, this.options.showParents);
      } else {
        this.traverseNode(node, 0);
      }
    });

    return this.output.join('\n');
  }

  private findNodesBySelector(document: Document, selector: string): Element[] {
    try {
      return Array.from(document.querySelectorAll(selector));
    } catch (error) {
      this.output.push(`Invalid CSS selector: "${selector}" "${error}"`);
      return [];
    }
  }

  private getNodePathWithIndices(node: Node): string {
    const path: string[] = [];
    let current: Node | null = node;

    while (current && current.nodeType === current.ELEMENT_NODE) {
      const element = current as Element;
      const tagName = element.tagName.toLowerCase();
      const childIndex = this.getChildIndex(element);

      let pathPart = tagName;
      if (element.className) {
        pathPart += `.${element.className.split(' ').join('.')}`;
      }
      if (childIndex > 0) {
        pathPart += `[${childIndex}]`;
      }

      path.unshift(pathPart);
      current = current.parentNode;
    }

    return path.join(' > ');
  }

  private getChildIndex(element: Element): number {
    if (!element.parentElement) return 0;

    let index = 1;
    let sibling = element.previousElementSibling;

    while (sibling) {
      index++;
      sibling = sibling.previousElementSibling;
    }

    return index;
  }

  private visualizeWithContext(node: Node, parentLevels: number): void {
    const ancestors: Node[] = [];
    let current: Node | null = node.parentNode;

    for (let i = 0; i < parentLevels && current; i++) {
      if (current.nodeType === current.ELEMENT_NODE) {
        ancestors.unshift(current);
        current = current.parentNode;
      }
    }

    ancestors.forEach((ancestor, index) => {
      const element = ancestor as Element;
      const indent = '  '.repeat(index);
      this.output.push(`${indent}<${element.tagName.toLowerCase()}> (parent context)`);
    });

    this.traverseNode(node, ancestors.length);
  }

  private traverseNode(node: Node, depth: number): void {
    if (depth > this.options.maxDepth!) {
      return;
    }

    const indent = '  '.repeat(depth);

    if (node.nodeType === node.ELEMENT_NODE) {
      const element = node as Element;
      const tagName = element.tagName.toLowerCase();

      let line = `${indent}<${tagName}`;

      if (this.options.showAttributes && element.attributes.length > 0) {
        // Suppress attributes for SVG and path elements to reduce output size
        const suppressAttributes = tagName === 'svg' || tagName === 'path';

        if (!suppressAttributes) {
          const attrs: string[] = [];

          if (element.id) {
            attrs.push(`id="${element.id}"`);
          }

          if (element.className) {
            attrs.push(`class="${element.className}"`);
          }

          for (const attr of Array.from(element.attributes)) {
            if (attr.name.startsWith('data-') ||
                (attr.name !== 'id' && attr.name !== 'class' && this.options.compact === false)) {
              attrs.push(`${attr.name}="${attr.value}"`);
            }
          }

          if (attrs.length > 0) {
            line += ` ${attrs.join(' ')}`;
          }
        }
      }

      line += '>';

      const childElements = Array.from(element.children);
      const textContent = this.getDirectTextContent(element);

      if (childElements.length === 0 && textContent && this.options.showTextNodes) {
        line += ` [TEXT: ${textContent.substring(0, 50)}${textContent.length > 50 ? '...' : ''}]`;
      }

      this.output.push(line);

      for (const child of element.childNodes) {
        this.traverseNode(child, depth + 1);
      }


    } else if (node.nodeType === node.TEXT_NODE && this.options.showTextNodes) {
      const text = node.textContent?.trim();
      if (text) {
        this.output.push(`${indent}[TEXT] ${text.substring(0, 100)}${text.length > 100 ? '...' : ''}`);
      }
    }
  }

  private getDirectTextContent(element: Element): string {
    let text = '';
    for (const child of element.childNodes) {
      if (child.nodeType === child.TEXT_NODE) {
        text += child.textContent || '';
      }
    }
    return text.trim();
  }
}

function parseArgs(args: string[]): { filePath?: string; options: VisualizerOptions } {
  const options: VisualizerOptions = {};
  let filePath: string | undefined;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === '--show-text') {
      options.showTextNodes = true;
    } else if (arg === '--no-attributes') {
      options.showAttributes = false;
    } else if (arg === '--full') {
      options.compact = false;
    } else if (arg === '--compact') {
      options.compact = true;
    } else if (arg === '--max-depth' && i + 1 < args.length) {
      options.maxDepth = parseInt(args[++i], 10);
    } else if (arg === '--output' && i + 1 < args.length) {
      options.outputFile = args[++i];
    } else if (arg === '--selector' && i + 1 < args.length) {
      options.selector = args[++i];
    } else if (arg === '--show-parents' && i + 1 < args.length) {
      options.showParents = parseInt(args[++i], 10);
    } else if (arg === '--highlight-path') {
      options.highlightPath = true;
    } else if (arg === '--match-index' && i + 1 < args.length) {
      options.matchIndex = parseInt(args[++i], 10);
    } else if (!arg.startsWith('--')) {
      filePath = arg;
    }
  }

  return { filePath, options };
}

function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help')) {
    console.log(`
DOM Hierarchy Visualizer

Usage: npx ts-node html-tree.ts <html-file> [options]

Options:
  --show-text         Show text nodes (hidden by default)
  --no-attributes     Hide element attributes
  --full              Show all attributes (not just id, class, data-*)
  --compact           Compact mode (default)
  --max-depth <n>     Maximum traversal depth
  --output <file>     Output to file instead of console
  --selector <css>    Start visualization from element(s) matching CSS selector
  --show-parents <n>  Show n levels of parent context above selected node(s)
  --highlight-path    Highlight the path from root to selected node(s)
  --match-index <n>   If multiple matches, show only the nth match (1-based)
  --help              Show this help message

Examples:
  npx ts-node html-tree.ts page.html --full
  npx ts-node html-tree.ts page.html --max-depth 3
  npx ts-node html-tree.ts page.html --show-text --output analysis.md
  npx ts-node html-tree.ts page.html --selector "article"
  npx ts-node html-tree.ts page.html --selector "article" --match-index 1
  npx ts-node html-tree.ts page.html --selector ".story" --show-parents 2 --highlight-path
    `);
    process.exit(0);
  }

  const { filePath, options } = parseArgs(args);

  if (!filePath) {
    console.error('Error: Please provide an HTML file path');
    process.exit(1);
  }

  const absolutePath = path.resolve(filePath);

  if (!fs.existsSync(absolutePath)) {
    console.error(`Error: File not found: ${absolutePath}`);
    process.exit(1);
  }

  try {
    const htmlContent = fs.readFileSync(absolutePath, 'utf-8');
    const visualizer = new DOMHierarchyVisualizer(options);
    const result = visualizer.visualize(htmlContent);

    if (options.outputFile) {
      fs.writeFileSync(options.outputFile, result, 'utf-8');
      console.log(`Output written to: ${options.outputFile}`);
    } else {
      console.log(result);
    }
  } catch (error) {
    console.error('Error processing file:', error);
    process.exit(1);
  }
}

// Check if running as main module
if (import.meta.main) {
  main();
}

export { DOMHierarchyVisualizer };
